# ABOUTME: Background worker for downloading Piper voice files from HuggingFace.
# ABOUTME: Handles chunked downloads with progress reporting and checksum verification.

"""DownloadWorker for downloading voice files from HuggingFace."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

import requests
from PySide6.QtCore import QObject, Signal

from gui.models.voice import Voice
from gui.utils.paths import VOICES_DIR

logger = logging.getLogger(__name__)

# HuggingFace base URL for Piper voice files
HUGGINGFACE_BASE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# Download chunk size: 64KB
CHUNK_SIZE = 65536


class DownloadWorker(QObject):
    """Worker for downloading voice files from HuggingFace.

    Downloads .onnx and .onnx.json files for a voice, verifies checksums,
    and stores them in the voices directory.

    Signals:
        progress(int): Download progress percentage (0-100)
        finished(bool): True if download succeeded
        error(str): Error message on failure
    """

    progress = Signal(int)
    finished = Signal(bool)
    error = Signal(str)

    def __init__(
        self,
        voice: Voice,
        voices_dir: Optional[Path] = None,
        parent: Optional[QObject] = None,
    ):
        """Initialise the DownloadWorker.

        Args:
            voice: The voice to download
            voices_dir: Directory to store voice files (default: VOICES_DIR)
            parent: Parent QObject
        """
        super().__init__(parent)
        self._voice = voice
        self._voices_dir = voices_dir or VOICES_DIR
        self._cancelled = False

    def run(self) -> None:
        """Download the voice files.

        Downloads both .onnx and .onnx.json files, verifying checksums.
        Emits progress updates and finished signal on completion.
        """
        try:
            # Create voice directory
            voice_dir = self._voices_dir / self._voice.language / self._voice.key
            voice_dir.mkdir(parents=True, exist_ok=True)

            # Calculate total size for progress
            total_size = self._voice.size_bytes
            downloaded = 0

            # Download each file
            for ext, file_info in self._voice.files.items():
                if self._cancelled:
                    self.finished.emit(False)
                    return

                filename = f"{self._voice.key}{ext}"
                url = f"{HUGGINGFACE_BASE_URL}/{self._voice.language}/{self._voice.key}/{filename}"
                target_path = voice_dir / filename
                expected_md5 = file_info.get("md5_digest", "")

                downloaded = self._download_file(
                    url, target_path, downloaded, total_size
                )

                # Verify checksum
                if expected_md5 and not self._verify_checksum(target_path, expected_md5):
                    logger.error("Checksum mismatch for %s", filename)
                    self.finished.emit(False)
                    return

            self.progress.emit(100)
            self.finished.emit(True)

        except Exception as e:
            logger.exception("Failed to download voice")
            self.error.emit(str(e))
            self.finished.emit(False)

    def _download_file(
        self, url: str, target_path: Path, downloaded: int, total_size: int
    ) -> int:
        """Download a single file with progress reporting.

        Uses atomic write: downloads to temp file then renames.

        Args:
            url: URL to download from
            target_path: Final path for the file
            downloaded: Bytes already downloaded (for overall progress)
            total_size: Total bytes to download

        Returns:
            Updated downloaded byte count
        """
        temp_path = target_path.with_suffix(target_path.suffix + ".tmp")

        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if self._cancelled:
                    temp_path.unlink(missing_ok=True)
                    return downloaded

                f.write(chunk)
                downloaded += len(chunk)

                # Emit progress
                if total_size > 0:
                    percent = int((downloaded / total_size) * 100)
                    self.progress.emit(min(percent, 99))  # Save 100 for final

        # Atomic rename
        temp_path.rename(target_path)

        return downloaded

    def _verify_checksum(self, file_path: Path, expected_md5: str) -> bool:
        """Verify file MD5 checksum.

        Args:
            file_path: Path to the file
            expected_md5: Expected MD5 hex digest

        Returns:
            True if checksum matches
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                md5_hash.update(chunk)

        actual_md5 = md5_hash.hexdigest()
        return actual_md5 == expected_md5

    def cancel(self) -> None:
        """Cancel the download."""
        self._cancelled = True
