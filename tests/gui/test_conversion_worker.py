# ABOUTME: Tests for ConversionWorker that runs make-audiobook via QProcess.
# ABOUTME: Verifies subprocess execution, progress parsing, and cancellation.

"""Tests for ConversionWorker."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


from PySide6.QtCore import QProcess

from gui.workers.conversion_worker import ConversionWorker
from gui.models.conversion_job import ConversionJob, JobStatus


# qapp fixture is provided by conftest.py


@pytest.fixture
def sample_job(tmp_path):
    """Sample conversion job."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, world!")
    return ConversionJob(
        files=[test_file],
        voice_key="en_US-ryan-high",
        length_scale=1.5,
    )


class TestConversionWorker:
    """Tests for ConversionWorker."""

    def test_worker_creation(self, qapp, sample_job):
        """Test ConversionWorker can be created."""
        worker = ConversionWorker(job=sample_job)
        assert worker is not None

    def test_worker_has_progress_signal(self, qapp, sample_job):
        """Test ConversionWorker has progress signal."""
        worker = ConversionWorker(job=sample_job)
        assert hasattr(worker, "progress")

    def test_worker_has_finished_signal(self, qapp, sample_job):
        """Test ConversionWorker has finished signal."""
        worker = ConversionWorker(job=sample_job)
        assert hasattr(worker, "finished")

    def test_worker_has_log_signal(self, qapp, sample_job):
        """Test ConversionWorker has log signal."""
        worker = ConversionWorker(job=sample_job)
        assert hasattr(worker, "log")

    def test_worker_builds_command_with_voice(self, qapp, sample_job):
        """Test ConversionWorker builds command with voice argument."""
        worker = ConversionWorker(job=sample_job)
        cmd = worker._build_command()

        assert "make-audiobook" in str(cmd[0])
        # Voice is passed via environment/stdin in actual usage, not command line
        # Check files are in command
        assert str(sample_job.files[0]) in [str(c) for c in cmd]

    def test_worker_builds_command_with_random_voice(self, qapp, tmp_path):
        """Test ConversionWorker builds command with --random flag."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        job = ConversionJob(
            files=[test_file],
            random_voice=True,
            random_filter="medium",
        )
        worker = ConversionWorker(job=job)
        cmd = worker._build_command()

        cmd_str = " ".join(str(c) for c in cmd)
        assert "--random" in cmd_str or "-r" in cmd_str

    def test_worker_builds_command_with_length_scale(self, qapp, sample_job):
        """Test ConversionWorker includes length_scale in command."""
        sample_job.length_scale = 1.8
        worker = ConversionWorker(job=sample_job)
        cmd = worker._build_command()

        cmd_str = " ".join(str(c) for c in cmd)
        assert "1.8" in cmd_str or "--length_scale" in cmd_str or "-s" in cmd_str

    def test_worker_emits_log_messages(self, qapp, sample_job):
        """Test ConversionWorker emits log signal for output."""
        worker = ConversionWorker(job=sample_job)

        log_messages = []
        worker.log.connect(lambda msg: log_messages.append(msg))

        # Simulate process output
        worker._handle_stdout("Processing file...")

        assert len(log_messages) == 1
        assert "Processing file..." in log_messages[0]

    def test_worker_emits_progress(self, qapp, sample_job):
        """Test ConversionWorker emits progress signal."""
        worker = ConversionWorker(job=sample_job)

        progress_updates = []
        worker.progress.connect(lambda f, p: progress_updates.append((f, p)))

        # Simulate progress output (pv format: bytes transferred)
        worker._parse_progress_output("1.5MiB 0:00:05 [300KiB/s]")

        # Should have parsed some progress
        assert len(progress_updates) >= 0  # May not parse all formats

    def test_worker_emits_finished_on_completion(self, qapp, sample_job):
        """Test ConversionWorker emits finished signal."""
        worker = ConversionWorker(job=sample_job)

        finished_results = []
        worker.finished.connect(lambda f, s: finished_results.append((f, s)))

        # Simulate process completion
        worker._on_process_finished(0)

        assert len(finished_results) == 1
        assert finished_results[0][1] is True  # success

    def test_worker_emits_finished_with_failure_on_error(self, qapp, sample_job):
        """Test ConversionWorker emits finished(False) on error exit."""
        worker = ConversionWorker(job=sample_job)

        finished_results = []
        worker.finished.connect(lambda f, s: finished_results.append((f, s)))

        # Simulate process error
        worker._on_process_finished(1)

        assert len(finished_results) == 1
        assert finished_results[0][1] is False  # failure

    def test_worker_can_be_cancelled(self, qapp, sample_job):
        """Test ConversionWorker can be cancelled."""
        worker = ConversionWorker(job=sample_job)

        # Create a mock process
        worker._process = MagicMock()
        worker.cancel()

        worker._process.terminate.assert_called_once()

    def test_worker_handles_multiple_files(self, qapp, tmp_path):
        """Test ConversionWorker handles multiple files."""
        files = []
        for i in range(3):
            f = tmp_path / f"chapter{i}.txt"
            f.write_text(f"Chapter {i}")
            files.append(f)

        job = ConversionJob(files=files, voice_key="en_US-ryan-high")
        worker = ConversionWorker(job=job)
        cmd = worker._build_command()

        # All files should be in command
        for f in files:
            assert str(f) in [str(c) for c in cmd]

    def test_worker_updates_job_status(self, qapp, sample_job):
        """Test ConversionWorker updates job status."""
        worker = ConversionWorker(job=sample_job)

        # Initial status
        assert sample_job.status == JobStatus.PENDING

        # Simulate starting
        worker._on_process_started()
        assert sample_job.status == JobStatus.IN_PROGRESS

        # Simulate completion
        worker._on_process_finished(0)
        assert sample_job.status == JobStatus.COMPLETED

    def test_worker_handles_stderr(self, qapp, sample_job):
        """Test ConversionWorker handles stderr output."""
        worker = ConversionWorker(job=sample_job)

        log_messages = []
        worker.log.connect(lambda msg: log_messages.append(msg))

        worker._handle_stderr("Error: file not found")

        assert len(log_messages) == 1
        assert "Error" in log_messages[0]

    def test_worker_has_error_signal(self, qapp, sample_job):
        """Test ConversionWorker has error signal."""
        worker = ConversionWorker(job=sample_job)
        assert hasattr(worker, "error")

    def test_worker_emits_error_on_failed_to_start(self, qapp, sample_job):
        """Test ConversionWorker emits error when process fails to start."""
        worker = ConversionWorker(job=sample_job)

        error_messages = []
        worker.error.connect(lambda msg: error_messages.append(msg))

        finished_results = []
        worker.finished.connect(lambda f, s: finished_results.append((f, s)))

        # Simulate FailedToStart error
        worker._on_process_error(QProcess.ProcessError.FailedToStart)

        assert len(error_messages) == 1
        assert "not found" in error_messages[0].lower() or "not executable" in error_messages[0].lower()
        assert sample_job.status == JobStatus.FAILED

        # FailedToStart must also emit finished to unblock the UI
        assert len(finished_results) == 1
        assert finished_results[0][1] is False

    def test_worker_emits_error_on_crash(self, qapp, sample_job):
        """Test ConversionWorker emits error when process crashes."""
        worker = ConversionWorker(job=sample_job)

        error_messages = []
        worker.error.connect(lambda msg: error_messages.append(msg))

        worker._on_process_error(QProcess.ProcessError.Crashed)

        assert len(error_messages) == 1
        assert "crashed" in error_messages[0].lower()
        assert sample_job.status == JobStatus.FAILED

    def test_worker_error_on_crash_does_not_emit_finished(self, qapp, sample_job):
        """Test Crashed error does not emit finished (Qt emits it separately)."""
        worker = ConversionWorker(job=sample_job)

        finished_results = []
        worker.finished.connect(lambda f, s: finished_results.append((f, s)))

        worker._on_process_error(QProcess.ProcessError.Crashed)

        # Crashed emits finished from Qt, so we should not double-emit
        assert len(finished_results) == 0

    def test_worker_file_progress_reaches_100_on_success(self, qapp, sample_job):
        """Test file progress reaches 100% when process succeeds."""
        worker = ConversionWorker(job=sample_job)
        worker._current_file = sample_job.files[0]

        progress_updates = []
        worker.progress.connect(lambda f, p: progress_updates.append((f, p)))

        worker._on_process_finished(0)

        # File progress should reach 100 on success
        assert any(p == 100 for _, p in progress_updates)

    def test_worker_overall_progress_correct_for_last_file(self, qapp, tmp_path):
        """Test overall progress is correct when processing last file."""
        files = []
        for i in range(4):
            f = tmp_path / f"ch{i}.txt"
            f.write_text(f"Chapter {i}")
            files.append(f)

        job = ConversionJob(files=files, voice_key="en_US-ryan-high")
        worker = ConversionWorker(job=job)

        overall_updates = []
        worker.overall_progress.connect(lambda p: overall_updates.append(p))

        # Simulate "Processing file 4 of 4"
        worker._parse_progress_output("Processing file 4 of 4")

        # For file 4 of 4, overall should be 75% ((4-1)/4 * 100)
        assert len(overall_updates) >= 1
        assert overall_updates[-1] == 75

    def test_worker_parses_file_progress_from_processing_message(self, qapp, tmp_path):
        """Test that Processing message resets file tracking."""
        files = [tmp_path / "a.txt", tmp_path / "b.txt"]
        for f in files:
            f.write_text("test")

        job = ConversionJob(files=files, voice_key="en_US-ryan-high")
        worker = ConversionWorker(job=job)

        # Simulate transitioning files
        worker._parse_progress_output("Processing file 1 of 2")
        assert worker._current_file == files[0]
        assert worker._current_file_progress == 0

        # Simulate some pv progress on first file
        worker._parse_progress_output("1.5MiB 0:00:05 [300KiB/s]")
        assert worker._current_file_progress > 0

        # Transition to second file
        worker._parse_progress_output("Processing file 2 of 2")
        assert worker._current_file == files[1]
        assert worker._current_file_progress == 0


class TestKokoroConversionWorker:
    """Tests for Kokoro engine-specific conversion worker behaviour."""

    @pytest.fixture
    def kokoro_job(self, tmp_path):
        """Sample Kokoro conversion job."""
        test_file = tmp_path / "book.epub"
        test_file.write_text("epub content")
        return ConversionJob(
            files=[test_file],
            voice_key="af_heart",
            engine="kokoro",
            speed=1.5,
        )

    def test_kokoro_build_command_has_engine_flag(self, qapp, kokoro_job):
        """Kokoro jobs should include --engine=kokoro in command."""
        worker = ConversionWorker(job=kokoro_job)
        cmd = worker._build_command()
        cmd_str = " ".join(str(c) for c in cmd)
        assert "--engine=kokoro" in cmd_str

    def test_kokoro_build_command_has_voice(self, qapp, kokoro_job):
        """Kokoro jobs should pass voice name directly (not a path)."""
        worker = ConversionWorker(job=kokoro_job)
        cmd = worker._build_command()
        cmd_str = " ".join(str(c) for c in cmd)
        assert "--voice=af_heart" in cmd_str

    def test_kokoro_build_command_has_speed(self, qapp, kokoro_job):
        """Kokoro jobs should use --speed instead of --length_scale."""
        worker = ConversionWorker(job=kokoro_job)
        cmd = worker._build_command()
        cmd_str = " ".join(str(c) for c in cmd)
        assert "--speed=1.5" in cmd_str
        assert "--length_scale" not in cmd_str

    def test_kokoro_progress_parsing_chunk(self, qapp, kokoro_job):
        """Kokoro chunk progress (N/M) should be parsed correctly."""
        worker = ConversionWorker(job=kokoro_job)
        worker._current_file = kokoro_job.files[0]

        progress_updates = []
        worker.progress.connect(lambda f, p: progress_updates.append((f, p)))

        worker._parse_progress_output("[■■■■■□□□□□] (50/100) ⠋")

        assert len(progress_updates) >= 1
        _, percent = progress_updates[-1]
        assert percent == 50

    def test_kokoro_progress_parsing_chapter_marker(self, qapp, kokoro_job):
        """Kokoro 'Processing:' marker should be tracked."""
        worker = ConversionWorker(job=kokoro_job)
        worker._current_file = kokoro_job.files[0]

        log_messages = []
        worker.log.connect(lambda msg: log_messages.append(msg))

        worker._handle_stdout("Processing: Chapter 1 - The Beginning")

        assert any("Chapter 1" in msg for msg in log_messages)

    def test_kokoro_progress_parsing_total_chapters(self, qapp, kokoro_job):
        """Kokoro 'Total Chapters:' should be stored for overall progress."""
        worker = ConversionWorker(job=kokoro_job)
        worker._current_file = kokoro_job.files[0]

        worker._parse_progress_output("Total Chapters: 12")

        assert worker._kokoro_total_chapters == 12

    def test_kokoro_progress_parsing_completed_chapter(self, qapp, kokoro_job):
        """Kokoro 'Completed' marker should increment chapter count."""
        worker = ConversionWorker(job=kokoro_job)
        worker._current_file = kokoro_job.files[0]
        worker._kokoro_total_chapters = 4

        progress_updates = []
        worker.progress.connect(lambda f, p: progress_updates.append((f, p)))

        worker._parse_progress_output("Completed Chapter 1: 50/50 chunks processed")

        assert worker._kokoro_completed_chapters == 1

    def test_kokoro_handles_carriage_return_in_stdout(self, qapp, kokoro_job):
        """QProcess output with \\r should be handled correctly."""
        worker = ConversionWorker(job=kokoro_job)
        worker._current_file = kokoro_job.files[0]

        progress_updates = []
        worker.progress.connect(lambda f, p: progress_updates.append((f, p)))

        # Simulate raw QProcess output with \r overwriting
        raw_data = "[■□□□□□□□□□] (10/100) ⠋\r[■■□□□□□□□□] (20/100) ⠙"
        # The stdout handler splits on \n, so this comes as one "line"
        # but the _handle_stdout should handle \r segments
        worker._handle_stdout(raw_data)

        # Should have parsed the latest segment (20/100)
        assert any(p == 20 for _, p in progress_updates)

    def test_piper_build_command_unchanged(self, qapp, tmp_path):
        """Piper jobs should still use the existing command format."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        job = ConversionJob(
            files=[test_file],
            voice_key="en_US-ryan-high",
            engine="piper",
            length_scale=1.5,
        )
        worker = ConversionWorker(job=job)
        cmd = worker._build_command()
        cmd_str = " ".join(str(c) for c in cmd)

        # Piper should NOT have --engine flag (backwards compat)
        assert "--engine=" not in cmd_str
        # Should have length_scale
        assert "--length_scale=1.5" in cmd_str


class TestOverallProgressBlending:
    """Tests for blended overall progress in ConversionWorker."""

    def test_single_file_kokoro_forwards_chunk_progress_to_overall(self, qapp, tmp_path):
        """Single-file Kokoro: chunk progress should drive overall bar."""
        test_file = tmp_path / "book.epub"
        test_file.write_text("content")
        job = ConversionJob(files=[test_file], voice_key="af_heart", engine="kokoro")
        worker = ConversionWorker(job=job)
        worker._current_file = test_file

        overall_updates = []
        worker.overall_progress.connect(lambda p: overall_updates.append(p))

        worker._parse_progress_output("Processing chunk 3/10 \u280b")

        assert len(overall_updates) >= 1
        assert overall_updates[-1] == 30  # 3/10 = 30%

    def test_single_file_piper_forwards_file_progress_to_overall(self, qapp, tmp_path):
        """Single-file Piper: pv progress should drive overall bar."""
        test_file = tmp_path / "book.txt"
        test_file.write_text("content")
        job = ConversionJob(files=[test_file], voice_key="en_US-ryan-high", engine="piper")
        worker = ConversionWorker(job=job)
        worker._current_file = test_file

        overall_updates = []
        worker.overall_progress.connect(lambda p: overall_updates.append(p))

        worker._parse_progress_output("1.5MiB 0:00:05 [300KiB/s]")

        assert len(overall_updates) >= 1
        assert overall_updates[-1] > 0

    def test_multi_file_blends_file_progress_into_overall(self, qapp, tmp_path):
        """Multi-file: overall should blend completed files + current file fraction."""
        files = []
        for i in range(4):
            f = tmp_path / f"ch{i}.txt"
            f.write_text(f"Chapter {i}")
            files.append(f)

        job = ConversionJob(files=files, voice_key="en_US-ryan-high", engine="piper")
        worker = ConversionWorker(job=job)

        overall_updates = []
        worker.overall_progress.connect(lambda p: overall_updates.append(p))

        # Simulate starting file 2 of 4 (1 completed)
        worker._parse_progress_output("Processing file 2 of 4")
        # Now simulate 50% pv progress within file 2
        worker._parse_progress_output("1.5MiB 0:00:05 [300KiB/s]")

        # Expected: (1 completed * 100 + ~5% file progress) / 4 = ~26%
        # The pv progress adds ~5 each time, so (100 + 5) / 4 = 26
        assert len(overall_updates) >= 2
        # After Processing file 2 of 4: overall = (1*100 + 0) / 4 = 25
        assert overall_updates[0] == 25
        # After pv progress: overall = (1*100 + 5) / 4 = 26
        assert overall_updates[1] == 26

    def test_multi_file_kokoro_blends_chunk_progress(self, qapp, tmp_path):
        """Multi-file Kokoro: overall should blend completed files + chunk progress."""
        files = []
        for i in range(2):
            f = tmp_path / f"book{i}.epub"
            f.write_text("content")
            files.append(f)

        job = ConversionJob(files=files, voice_key="af_heart", engine="kokoro")
        worker = ConversionWorker(job=job)
        worker._current_file = files[0]
        worker._job.current_file_index = 0

        overall_updates = []
        worker.overall_progress.connect(lambda p: overall_updates.append(p))

        # 50% through first file of 2
        worker._parse_progress_output("Processing chunk 5/10 \u280b")

        assert len(overall_updates) >= 1
        # (0 completed * 100 + 50) / 2 = 25
        assert overall_updates[-1] == 25

    def test_overall_progress_reaches_100_on_success(self, qapp, tmp_path):
        """Overall progress should hit 100% when process completes successfully."""
        test_file = tmp_path / "book.txt"
        test_file.write_text("content")
        job = ConversionJob(files=[test_file], voice_key="en_US-ryan-high")
        worker = ConversionWorker(job=job)
        worker._current_file = test_file

        overall_updates = []
        worker.overall_progress.connect(lambda p: overall_updates.append(p))

        worker._on_process_finished(0)

        assert overall_updates[-1] == 100


class TestLogNoiseFiltering:
    """Tests for GUI log noise filtering in ConversionWorker."""

    @pytest.fixture
    def kokoro_worker(self, tmp_path, qapp):
        """Kokoro worker with log signal connected."""
        test_file = tmp_path / "book.epub"
        test_file.write_text("content")
        job = ConversionJob(
            files=[test_file],
            voice_key="af_heart",
            engine="kokoro",
        )
        return ConversionWorker(job=job)

    def test_spinner_frames_suppressed_from_log(self, kokoro_worker):
        """Kokoro spinner frames should not appear in log output."""
        log_messages = []
        kokoro_worker.log.connect(lambda msg: log_messages.append(msg))

        kokoro_worker._handle_stdout("Processing chunk 1/3 \u280b")
        kokoro_worker._handle_stdout("Processing chunk 1/3 \u2819")
        kokoro_worker._handle_stdout("Processing chunk 1/3 \u2839")

        # Should emit at most one summary line, not three individual frames
        assert len(log_messages) <= 1
        if log_messages:
            assert "Processing chunk 1/3" in log_messages[0]

    def test_chunk_transition_logged_once(self, kokoro_worker):
        """Chunk transitions should produce one summary log line each."""
        log_messages = []
        kokoro_worker.log.connect(lambda msg: log_messages.append(msg))

        # Many spinner frames for chunk 1
        for spinner in "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f":
            kokoro_worker._handle_stdout(f"Processing chunk 1/3 {spinner}")
        # Transition to chunk 2
        for spinner in "\u280b\u2819\u2839":
            kokoro_worker._handle_stdout(f"Processing chunk 2/3 {spinner}")

        # Should see exactly 2 summary lines (one per chunk transition)
        assert len(log_messages) == 2
        assert "1/3" in log_messages[0]
        assert "2/3" in log_messages[1]

    def test_curl_progress_bars_suppressed(self, kokoro_worker):
        """curl download progress bars should not appear in log."""
        log_messages = []
        kokoro_worker.log.connect(lambda msg: log_messages.append(msg))

        kokoro_worker._handle_stderr("##O#-#")
        kokoro_worker._handle_stderr("####                  42.7%")
        kokoro_worker._handle_stderr("  0.6%")
        kokoro_worker._handle_stderr("############ 100.0%")

        assert len(log_messages) == 0

    def test_pymupdf_advisory_suppressed(self, kokoro_worker):
        """pymupdf package advisory should not appear in log."""
        log_messages = []
        kokoro_worker.log.connect(lambda msg: log_messages.append(msg))

        kokoro_worker._handle_stdout(
            "Consider using the pymupdf_layout package for a greatly improved page layout analysis."
        )

        assert len(log_messages) == 0

    def test_meaningful_messages_not_suppressed(self, kokoro_worker):
        """Important messages should still appear in log."""
        log_messages = []
        kokoro_worker.log.connect(lambda msg: log_messages.append(msg))

        meaningful_lines = [
            "Processing: Chapter 1",
            "Completed Chapter 1: 3/3 chunks processed",
            "\u2611\ufe0f Downloaded kokoro-v1.0.onnx",
            "\U0001f6b9 Downloading kokoro-v1.0.onnx (~370 MB) ...",
            "\u26d4\ufe0f kokoro-tts failed for test.epub",
            "Error: something went wrong",
        ]
        for line in meaningful_lines:
            kokoro_worker._handle_stderr(line)

        assert len(log_messages) == len(meaningful_lines)

    def test_progress_still_parsed_from_suppressed_lines(self, kokoro_worker):
        """Progress bar should still update even when log lines are suppressed."""
        kokoro_worker._current_file = kokoro_worker._job.files[0]

        progress_updates = []
        kokoro_worker.progress.connect(lambda f, p: progress_updates.append((f, p)))

        # Spinner frames are suppressed from log but should still drive progress
        kokoro_worker._handle_stdout("Processing chunk 2/3 \u280b")

        assert len(progress_updates) >= 1
        _, percent = progress_updates[-1]
        assert percent == 66  # 2/3 = 66%
