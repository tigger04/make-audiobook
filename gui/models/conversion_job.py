# ABOUTME: Data model for audiobook conversion jobs.
# ABOUTME: Tracks job state, progress, and settings for batch conversions.

"""ConversionJob data model for tracking audiobook conversions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class JobStatus(Enum):
    """Status states for a conversion job."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ConversionJob:
    """Represents a batch of files to convert to audiobooks.

    Attributes:
        files: List of input file paths to convert
        voice_key: Voice identifier (e.g., "en_US-ryan-high"), or None for selection
        random_voice: Use random voice selection
        random_filter: Quality filter when using random voice (e.g., "medium")
        length_scale: Speech speed (1.0 = normal, higher = slower)
        author: ID3 author tag value
        title: ID3 album/book title tag value
        status: Current job status
        progress: Overall progress percentage (0-100)
        current_file_index: Index of file currently being processed
        log_messages: List of log entries from conversion
        error_message: Error description if job failed
        output_files: List of generated output file paths
    """

    files: list[Path]
    voice_key: Optional[str] = None
    random_voice: bool = False
    random_filter: Optional[str] = None
    length_scale: float = 1.5
    author: Optional[str] = None
    title: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    current_file_index: Optional[int] = None
    log_messages: list[str] = field(default_factory=list)
    error_message: Optional[str] = None
    output_files: list[Path] = field(default_factory=list)

    def get_current_file(self) -> Optional[Path]:
        """Return the file currently being processed, or None."""
        if self.current_file_index is None:
            return None
        if self.current_file_index < 0 or self.current_file_index >= len(self.files):
            return None
        return self.files[self.current_file_index]

    def add_log(self, message: str) -> None:
        """Add a log message to the job history."""
        self.log_messages.append(message)

    @property
    def file_count(self) -> int:
        """Return the number of files in this job."""
        return len(self.files)
