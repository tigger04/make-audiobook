# ABOUTME: Tests for DownloadWorker that downloads voice files from HuggingFace.
# ABOUTME: Verifies chunked download, progress, and checksum verification.

"""Tests for DownloadWorker."""

import hashlib
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from PySide6.QtCore import QCoreApplication

from gui.workers.download_worker import DownloadWorker
from gui.models.voice import Voice


@pytest.fixture(scope="module")
def qapp():
    """Provide a QApplication for signal/slot testing."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@pytest.fixture
def sample_voice():
    """Sample voice to download."""
    return Voice(
        key="en_US-ryan-high",
        name="Ryan",
        language="en_US",
        quality="high",
        files={
            ".onnx": {"size_bytes": 1000, "md5_digest": "abc123"},
            ".onnx.json": {"size_bytes": 100, "md5_digest": "def456"},
        },
        size_bytes=1100,
    )


@pytest.fixture
def voices_dir(tmp_path):
    """Provide a temporary voices directory."""
    voices = tmp_path / "voices"
    voices.mkdir()
    return voices


class TestDownloadWorker:
    """Tests for DownloadWorker."""

    def test_worker_creation(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker can be created."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)
        assert worker is not None

    def test_worker_has_progress_signal(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker has progress signal."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)
        assert hasattr(worker, "progress")

    def test_worker_has_finished_signal(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker has finished signal."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)
        assert hasattr(worker, "finished")

    def test_worker_has_error_signal(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker has error signal."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)
        assert hasattr(worker, "error")

    def test_worker_creates_voice_directory(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker creates the voice directory."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)

        # Create mock response with fake file content
        content = b"fake model content"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": str(len(content))}
        mock_response.iter_content.return_value = [content]

        with patch("gui.workers.download_worker.requests.get", return_value=mock_response):
            with patch.object(worker, "_verify_checksum", return_value=True):
                worker.run()

        voice_dir = voices_dir / "en_US" / "en_US-ryan-high"
        assert voice_dir.exists()

    def test_worker_downloads_onnx_file(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker downloads .onnx file."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)

        content = b"fake model content"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": str(len(content))}
        mock_response.iter_content.return_value = [content]

        with patch("gui.workers.download_worker.requests.get", return_value=mock_response):
            with patch.object(worker, "_verify_checksum", return_value=True):
                worker.run()

        onnx_file = voices_dir / "en_US" / "en_US-ryan-high" / "en_US-ryan-high.onnx"
        assert onnx_file.exists()

    def test_worker_emits_progress(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker emits progress signals."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)

        received_progress = []
        worker.progress.connect(lambda p: received_progress.append(p))

        # Simulate chunked download
        chunk_size = 250
        total_size = 1000
        chunks = [b"x" * chunk_size] * (total_size // chunk_size)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": str(total_size)}
        mock_response.iter_content.return_value = chunks

        with patch("gui.workers.download_worker.requests.get", return_value=mock_response):
            with patch.object(worker, "_verify_checksum", return_value=True):
                worker.run()

        # Should have received progress updates
        assert len(received_progress) > 0
        # Final progress should be around 100%
        assert max(received_progress) >= 90

    def test_worker_emits_finished_on_success(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker emits finished(True) on success."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)

        finished_results = []
        worker.finished.connect(lambda success: finished_results.append(success))

        content = b"fake model content"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": str(len(content))}
        mock_response.iter_content.return_value = [content]

        with patch("gui.workers.download_worker.requests.get", return_value=mock_response):
            with patch.object(worker, "_verify_checksum", return_value=True):
                worker.run()

        assert finished_results == [True]

    def test_worker_emits_error_on_network_failure(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker emits error signal on network failure."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)

        received_errors = []
        worker.error.connect(lambda e: received_errors.append(e))

        with patch("gui.workers.download_worker.requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            worker.run()

        assert len(received_errors) == 1
        assert "Connection refused" in received_errors[0]

    def test_worker_emits_error_on_checksum_failure(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker emits error on checksum mismatch."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)

        finished_results = []
        worker.finished.connect(lambda success: finished_results.append(success))

        content = b"corrupted content"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": str(len(content))}
        mock_response.iter_content.return_value = [content]

        with patch("gui.workers.download_worker.requests.get", return_value=mock_response):
            with patch.object(worker, "_verify_checksum", return_value=False):
                worker.run()

        assert finished_results == [False]

    def test_verify_checksum_with_valid_md5(self, qapp, sample_voice, voices_dir):
        """Test _verify_checksum returns True for valid MD5."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)

        # Create a file with known content
        test_file = voices_dir / "test.txt"
        content = b"hello world"
        test_file.write_bytes(content)
        expected_md5 = hashlib.md5(content).hexdigest()

        result = worker._verify_checksum(test_file, expected_md5)
        assert result is True

    def test_verify_checksum_with_invalid_md5(self, qapp, sample_voice, voices_dir):
        """Test _verify_checksum returns False for invalid MD5."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)

        test_file = voices_dir / "test.txt"
        test_file.write_bytes(b"hello world")

        result = worker._verify_checksum(test_file, "invalid_checksum")
        assert result is False

    def test_worker_uses_atomic_write(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker writes to temp file then renames."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)

        content = b"model content"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": str(len(content))}
        mock_response.iter_content.return_value = [content]

        temp_files_seen = []

        original_rename = Path.rename

        def track_rename(self, target):
            if ".tmp" in str(self):
                temp_files_seen.append(str(self))
            return original_rename(self, target)

        with patch("gui.workers.download_worker.requests.get", return_value=mock_response):
            with patch.object(worker, "_verify_checksum", return_value=True):
                with patch.object(Path, "rename", track_rename):
                    worker.run()

        # Should have used temp files that were renamed
        assert len(temp_files_seen) >= 1

    def test_worker_can_be_cancelled(self, qapp, sample_voice, voices_dir):
        """Test DownloadWorker respects cancellation."""
        worker = DownloadWorker(voice=sample_voice, voices_dir=voices_dir)
        worker.cancel()
        assert worker._cancelled is True
