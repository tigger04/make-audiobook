# ABOUTME: Tests for ConversionJob data model.
# ABOUTME: Verifies job state management and progress tracking.

"""Tests for ConversionJob model."""

import pytest
from pathlib import Path

from gui.models.conversion_job import ConversionJob, JobStatus


class TestJobStatus:
    """Tests for JobStatus enum."""

    def test_status_values(self):
        """Test all expected status values exist."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.IN_PROGRESS.value == "in_progress"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"


class TestConversionJob:
    """Tests for ConversionJob dataclass."""

    def test_job_creation_with_files(self):
        """Test ConversionJob can be created with file list."""
        files = [Path("/tmp/book.epub"), Path("/tmp/chapter.txt")]
        job = ConversionJob(files=files)
        assert job.files == files
        assert job.voice_key is None
        assert job.status == JobStatus.PENDING
        assert job.progress == 0

    def test_job_default_status_is_pending(self):
        """Test new jobs default to PENDING status."""
        job = ConversionJob(files=[])
        assert job.status == JobStatus.PENDING

    def test_job_with_voice_key(self):
        """Test ConversionJob with specified voice."""
        job = ConversionJob(
            files=[Path("/tmp/test.txt")],
            voice_key="en_US-ryan-high",
        )
        assert job.voice_key == "en_US-ryan-high"

    def test_job_with_settings(self):
        """Test ConversionJob with custom settings."""
        job = ConversionJob(
            files=[Path("/tmp/test.txt")],
            length_scale=1.8,
            author="Jane Austen",
            title="Pride and Prejudice",
        )
        assert job.length_scale == 1.8
        assert job.author == "Jane Austen"
        assert job.title == "Pride and Prejudice"

    def test_job_default_length_scale(self):
        """Test default length_scale is 1.0 (normal speed)."""
        job = ConversionJob(files=[])
        assert job.length_scale == 1.0

    def test_job_random_voice_flag(self):
        """Test random voice selection flag."""
        job = ConversionJob(files=[], random_voice=True, random_filter="medium")
        assert job.random_voice is True
        assert job.random_filter == "medium"

    def test_job_progress_update(self):
        """Test job progress can be updated."""
        job = ConversionJob(files=[Path("/tmp/test.txt")])
        job.progress = 50
        job.status = JobStatus.IN_PROGRESS
        assert job.progress == 50
        assert job.status == JobStatus.IN_PROGRESS

    def test_job_current_file_tracking(self):
        """Test tracking of current file being processed."""
        files = [Path("/tmp/ch1.txt"), Path("/tmp/ch2.txt")]
        job = ConversionJob(files=files)
        job.current_file_index = 0
        assert job.get_current_file() == files[0]
        job.current_file_index = 1
        assert job.get_current_file() == files[1]

    def test_job_current_file_none_when_no_index(self):
        """Test get_current_file returns None when no index set."""
        job = ConversionJob(files=[Path("/tmp/test.txt")])
        assert job.get_current_file() is None

    def test_job_current_file_none_when_index_out_of_range(self):
        """Test get_current_file returns None for invalid index."""
        job = ConversionJob(files=[Path("/tmp/test.txt")])
        job.current_file_index = 5
        assert job.get_current_file() is None

    def test_job_log_messages(self):
        """Test job can store log messages."""
        job = ConversionJob(files=[])
        job.add_log("Starting conversion...")
        job.add_log("Processing file 1")
        assert len(job.log_messages) == 2
        assert job.log_messages[0] == "Starting conversion..."

    def test_job_error_message(self):
        """Test job stores error message on failure."""
        job = ConversionJob(files=[Path("/tmp/test.txt")])
        job.status = JobStatus.FAILED
        job.error_message = "File not found"
        assert job.error_message == "File not found"

    def test_job_output_files(self):
        """Test job tracks output files."""
        job = ConversionJob(files=[Path("/tmp/ch1.txt")])
        job.output_files.append(Path("/tmp/ch1.mp3"))
        assert job.output_files == [Path("/tmp/ch1.mp3")]

    def test_job_file_count(self):
        """Test job file count property."""
        job = ConversionJob(files=[Path("/tmp/a.txt"), Path("/tmp/b.txt")])
        assert job.file_count == 2
