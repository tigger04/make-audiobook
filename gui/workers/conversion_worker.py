# ABOUTME: Background worker for running make-audiobook conversions via QProcess.
# ABOUTME: Wraps subprocess execution with progress parsing and cancellation.

"""ConversionWorker for running make-audiobook as a subprocess."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QProcess, Signal

from gui.models.conversion_job import ConversionJob, JobStatus
from gui.utils.paths import get_script_path

logger = logging.getLogger(__name__)


class ConversionWorker(QObject):
    """Worker for running make-audiobook conversions.

    Runs the make-audiobook script as a subprocess via QProcess.
    Parses output for progress updates and handles cancellation.

    Signals:
        progress(str, int): Filename and progress percentage
        finished(str, bool): Filename and success status
        log(str): Log message from process output
    """

    progress = Signal(str, int)
    finished = Signal(str, bool)
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

    def start(self) -> None:
        """Start the conversion process.

        Creates a QProcess and runs make-audiobook with job parameters.
        """
        self._process = QProcess(self)
        self._process.readyReadStandardOutput.connect(self._on_stdout_ready)
        self._process.readyReadStandardError.connect(self._on_stderr_ready)
        self._process.started.connect(self._on_process_started)
        self._process.finished.connect(self._on_process_finished)

        cmd = self._build_command()
        program = str(cmd[0])
        args = [str(a) for a in cmd[1:]]

        logger.info("Starting conversion: %s %s", program, " ".join(args))
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

        Returns:
            List of command and arguments
        """
        script_path = get_script_path()
        cmd: list[Path | str] = [script_path]

        # Add random voice flag
        if self._job.random_voice:
            if self._job.random_filter:
                cmd.append(f"--random={self._job.random_filter}")
            else:
                cmd.append("--random")

        # Add length scale
        if self._job.length_scale != 1.0:
            cmd.append(f"--length_scale={self._job.length_scale}")

        # Add files
        for f in self._job.files:
            cmd.append(f)

        return cmd

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

    def _handle_stdout(self, line: str) -> None:
        """Process a line of stdout output."""
        self.log.emit(line)
        self._parse_progress_output(line)

    def _handle_stderr(self, line: str) -> None:
        """Process a line of stderr output."""
        self.log.emit(line)
        self._parse_progress_output(line)

    def _parse_progress_output(self, line: str) -> None:
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
                overall = int((current - 1) / total * 100)
                self.progress.emit(str(self._current_file), overall)

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
        else:
            self._job.status = JobStatus.FAILED
            self._job.error_message = f"Process exited with code {exit_code}"

        filename = str(self._current_file) if self._current_file else ""
        self.finished.emit(filename, success)

    def cancel(self) -> None:
        """Cancel the conversion process."""
        if self._process is not None:
            self._job.status = JobStatus.CANCELLED
            self._process.terminate()
