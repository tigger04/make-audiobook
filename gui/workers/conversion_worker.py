# ABOUTME: Background worker for running make-audiobook conversions via QProcess.
# ABOUTME: Wraps subprocess execution with progress parsing and cancellation.

"""ConversionWorker for running make-audiobook as a subprocess."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, Signal

from gui.models.conversion_job import ConversionJob, JobStatus
from gui.utils.paths import get_script_path, get_expanded_path, VOICES_DIR

logger = logging.getLogger(__name__)


# Lines matching these patterns are progress noise — parsed for the progress
# bar but suppressed from the log panel to keep it readable.
_NOISE_PATTERNS = [
    # Kokoro spinner frames: "Processing chunk 1/3 ⠋" (braille U+2800..U+28FF)
    re.compile(r"^Processing chunk \d+/\d+\s+[\u2800-\u28FF]"),
    # curl progress bars: "####  42.7%" or "##O#-#" or bare percentages
    re.compile(r"^[#=O\-\s]+\d*\.?\d*%?\s*$"),
    re.compile(r"^\s*\d+\.\d+%\s*$"),
    # pymupdf advisory (not an error, just noise)
    re.compile(r"^Consider using the pymupdf_layout package"),
]


class ConversionWorker(QObject):
    """Worker for running make-audiobook conversions.

    Runs the make-audiobook script as a subprocess via QProcess.
    Parses output for progress updates and handles cancellation.

    Signals:
        progress(str, int): Filename and file-level progress percentage
        overall_progress(int): Overall progress percentage across all files
        finished(str, bool): Filename and success status
        error(str): Human-readable error message
        log(str): Log message from process output
    """

    progress = Signal(str, int)
    overall_progress = Signal(int)
    finished = Signal(str, bool)
    error = Signal(str)
    log = Signal(str)

    def __init__(
        self,
        job: ConversionJob,
        parent: Optional[QObject] = None,
    ):
        """Initialise the ConversionWorker.

        Args:
            job: The conversion job to process
            parent: Parent QObject
        """
        super().__init__(parent)
        self._job = job
        self._process: Optional[QProcess] = None
        self._current_file: Optional[Path] = None
        self._current_file_progress = 0
        # Kokoro-specific progress tracking
        self._kokoro_total_chapters = 0
        self._kokoro_completed_chapters = 0
        self._last_logged_chunk: Optional[str] = None

    def start(self) -> None:
        """Start the conversion process.

        Creates a QProcess and runs make-audiobook with job parameters.
        Sets up expanded PATH to find dependencies when running from .app bundle.
        """
        self._process = QProcess(self)
        self._process.readyReadStandardOutput.connect(self._on_stdout_ready)
        self._process.readyReadStandardError.connect(self._on_stderr_ready)
        self._process.started.connect(self._on_process_started)
        self._process.finished.connect(self._on_process_finished)
        self._process.errorOccurred.connect(self._on_process_error)

        # Set up environment with expanded PATH for macOS app bundle
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PATH", get_expanded_path())
        self._process.setProcessEnvironment(env)

        cmd = self._build_command()
        program = str(cmd[0])
        args = [str(a) for a in cmd[1:]]

        logger.info("Starting conversion: %s %s", program, " ".join(args))
        logger.debug("PATH: %s", env.value("PATH"))
        self.log.emit(f"Running: {program} {' '.join(args)}")
        self._process.start(program, args)

    def run(self) -> None:
        """Run the conversion synchronously (for testing).

        In production, use start() for async execution.
        """
        # This is a simplified sync version for testing
        # In real usage, start() should be used with event loop
        self.start()

    def _build_command(self) -> list[Path | str]:
        """Build the command line for make-audiobook.

        Builds engine-specific command arguments:
        - Piper: --voice=path/to.onnx --length_scale=X (existing behaviour)
        - Kokoro: --engine=kokoro --voice=af_heart --speed=X
        - WhisperSpeech: --engine=whisperspeech

        Returns:
            List of command and arguments
        """
        script_path = get_script_path()
        cmd: list[Path | str] = [script_path]

        # Always use non-interactive mode in GUI
        cmd.append("--non-interactive")

        engine = self._job.engine

        # Add engine flag for non-default engines
        if engine != "piper":
            cmd.append(f"--engine={engine}")

        # Add author if specified
        if self._job.author:
            cmd.append(f"--author={self._job.author}")

        # Add title if specified
        if self._job.title:
            cmd.append(f"--title={self._job.title}")

        if engine == "kokoro":
            # Kokoro: pass voice name directly (not a file path)
            if self._job.voice_key:
                cmd.append(f"--voice={self._job.voice_key}")
            # Kokoro uses --speed directly (no inversion)
            if self._job.speed != 1.0:
                cmd.append(f"--speed={self._job.speed}")
        else:
            # Piper/WhisperSpeech: existing voice path resolution
            if not self._job.random_voice and self._job.voice_key:
                voice_path = self._resolve_voice_path(self._job.voice_key)
                if voice_path:
                    cmd.append(f"--voice={voice_path}")

            # Add random voice flag (Piper only)
            if self._job.random_voice:
                if self._job.random_filter:
                    cmd.append(f"--random={self._job.random_filter}")
                else:
                    cmd.append("--random")

            # Add length scale (Piper)
            if self._job.length_scale != 1.0:
                cmd.append(f"--length_scale={self._job.length_scale}")

        # Add files
        for f in self._job.files:
            cmd.append(f)

        return cmd

    def _resolve_voice_path(self, voice_key: str) -> Optional[str]:
        """Resolve a voice key to its full .onnx file path.

        Args:
            voice_key: Voice identifier like "en_US-ryan-high"

        Returns:
            Full path to .onnx file, or None if not found
        """
        if not voice_key:
            return None

        # Extract language from voice key (first part before first dash)
        parts = voice_key.split("-")
        if len(parts) < 2:
            return None
        language = parts[0]

        # Build expected path: VOICES_DIR/language/voice_key/voice_key.onnx
        voice_path = VOICES_DIR / language / voice_key / f"{voice_key}.onnx"

        if voice_path.exists():
            return str(voice_path)

        # Log warning but don't fail - let the script handle the error
        logger.warning("Voice file not found: %s", voice_path)
        return None

    def _on_stdout_ready(self) -> None:
        """Handle stdout data from process."""
        if self._process is None:
            return

        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line.strip():
                self._handle_stdout(line)

    def _on_stderr_ready(self) -> None:
        """Handle stderr data from process."""
        if self._process is None:
            return

        data = self._process.readAllStandardError().data().decode("utf-8", errors="replace")
        for line in data.splitlines():
            if line.strip():
                self._handle_stderr(line)

    def _is_noise(self, line: str) -> bool:
        """Check whether a line is progress noise that should not appear in the log."""
        return any(p.search(line) for p in _NOISE_PATTERNS)

    def _log_if_meaningful(self, line: str) -> None:
        """Emit line to log only if it carries meaningful information.

        Suppresses spinner frames and progress bars.  On chunk transitions
        (e.g. 1/3 -> 2/3) emits a single summary line instead of hundreds
        of spinner updates.
        """
        if self._is_noise(line):
            # Still check for chunk transitions to log a summary
            chunk_match = re.search(r"Processing chunk (\d+/\d+)", line)
            if chunk_match:
                chunk_id = chunk_match.group(1)
                if chunk_id != self._last_logged_chunk:
                    self._last_logged_chunk = chunk_id
                    self.log.emit(f"Processing chunk {chunk_id} ...")
            return
        self.log.emit(line)

    def _handle_line(self, line: str) -> None:
        """Process a single line: filter log noise, then parse for progress."""
        self._log_if_meaningful(line)
        self._parse_progress_output(line)

    def _handle_stdout(self, line: str) -> None:
        """Process a line of stdout output.

        Handles carriage returns (\\r) used by Kokoro for progress overwriting.
        Takes the last \\r segment as the current state of the line.
        """
        # Handle \r-separated segments (Kokoro overwrites progress lines)
        if "\r" in line:
            segments = line.split("\r")
            for segment in segments:
                stripped = segment.strip()
                if stripped:
                    self._handle_line(stripped)
        else:
            self._handle_line(line)

    def _handle_stderr(self, line: str) -> None:
        """Process a line of stderr output."""
        self._handle_line(line)

    def _parse_progress_output(self, line: str) -> None:
        """Parse progress from subprocess output.

        Handles both Piper (pv-style) and Kokoro (chunk-based) progress formats.
        """
        if self._job.engine == "kokoro":
            self._parse_kokoro_progress(line)
        else:
            self._parse_piper_progress(line)

    def _parse_piper_progress(self, line: str) -> None:
        """Parse progress from pv output or make-audiobook status.

        pv output format: "1.5MiB 0:00:05 [300KiB/s]"
        """
        # Look for pv-style progress (bytes transferred)
        pv_match = re.search(r"(\d+(?:\.\d+)?)\s*(B|KiB|MiB|GiB)", line)
        if pv_match:
            # Progress parsing is approximate; exact progress needs file size
            self._current_file_progress = min(self._current_file_progress + 5, 95)
            if self._current_file:
                self.progress.emit(str(self._current_file), self._current_file_progress)

        # Look for "Processing file N of M" pattern
        file_match = re.search(r"Processing file (\d+) of (\d+)", line)
        if file_match:
            current = int(file_match.group(1))
            total = int(file_match.group(2))
            if current <= len(self._job.files):
                self._current_file = self._job.files[current - 1]
                self._current_file_progress = 0
                self.progress.emit(str(self._current_file), 0)
                overall = int((current - 1) / total * 100)
                self.overall_progress.emit(overall)

    def _parse_kokoro_progress(self, line: str) -> None:
        """Parse progress from Kokoro CLI output.

        Kokoro progress formats:
        - Chunk progress: [■■■□□□] (N/M) ⠋
        - Chapter start: Processing: Chapter Title
        - Chapter done: Completed Chapter Title: N/M chunks processed
        - Total chapters: Total Chapters: N
        """
        # Parse chunk progress: "(N/M)" or "Processing chunk N/M"
        chunk_match = re.search(r"(?:chunk\s+|\()(\d+)/(\d+)\)?", line)
        if chunk_match:
            current_chunk = int(chunk_match.group(1))
            total_chunks = int(chunk_match.group(2))
            if total_chunks > 0:
                percent = int(current_chunk / total_chunks * 100)
                self._current_file_progress = percent
                if self._current_file:
                    self.progress.emit(str(self._current_file), percent)
            return

        # Parse total chapters count
        total_match = re.search(r"Total Chapters:\s*(\d+)", line)
        if total_match:
            self._kokoro_total_chapters = int(total_match.group(1))
            return

        # Parse completed chapter marker
        completed_match = re.search(r"^Completed .+:\s*\d+/\d+ chunks processed", line)
        if completed_match:
            self._kokoro_completed_chapters = self._kokoro_completed_chapters + 1
            return

    def _on_process_started(self) -> None:
        """Handle process start."""
        self._job.status = JobStatus.IN_PROGRESS
        if self._job.files:
            self._current_file = self._job.files[0]
            self._job.current_file_index = 0

    def _on_process_finished(self, exit_code: int) -> None:
        """Handle process completion."""
        success = exit_code == 0

        if success:
            self._job.status = JobStatus.COMPLETED
            # Set file progress to 100% on success
            if self._current_file:
                self.progress.emit(str(self._current_file), 100)
        else:
            self._job.status = JobStatus.FAILED
            self._job.error_message = f"Process exited with code {exit_code}"

        filename = str(self._current_file) if self._current_file else ""
        self.finished.emit(filename, success)

    _PROCESS_ERROR_MESSAGES = {
        QProcess.ProcessError.FailedToStart: "Script not found or not executable",
        QProcess.ProcessError.Crashed: "Conversion process crashed",
        QProcess.ProcessError.Timedout: "Conversion process timed out",
        QProcess.ProcessError.WriteError: "Could not send data to process",
        QProcess.ProcessError.ReadError: "Could not read process output",
        QProcess.ProcessError.UnknownError: "Unknown process error",
    }

    def _on_process_error(self, error_code: QProcess.ProcessError) -> None:
        """Handle QProcess errors (e.g., script not found).

        FailedToStart does not emit finished(), so we must emit
        both error and finished signals here to unblock the UI.
        """
        message = self._PROCESS_ERROR_MESSAGES.get(error_code, f"Process error {error_code}")
        logger.error("QProcess error: %s", message)
        self._job.status = JobStatus.FAILED
        self._job.error_message = message
        self.error.emit(message)

        # FailedToStart never emits finished(), so emit it here
        if error_code == QProcess.ProcessError.FailedToStart:
            filename = str(self._current_file) if self._current_file else ""
            self.finished.emit(filename, False)

    def cancel(self) -> None:
        """Cancel the conversion process."""
        if self._process is not None:
            self._job.status = JobStatus.CANCELLED
            self._process.terminate()
