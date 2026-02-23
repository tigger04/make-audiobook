# ABOUTME: Progress panel widget for displaying conversion progress.
# ABOUTME: Shows per-file and overall progress bars with log output.

"""ProgressPanel for displaying conversion progress."""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QGroupBox,
)

logger = logging.getLogger(__name__)


class ProgressPanel(QWidget):
    """Widget for displaying conversion progress.

    Shows:
    - Current file being processed
    - Per-file progress bar
    - Overall progress bar
    - Log output area
    - Cancel button

    Signals:
        cancelRequested: Emitted when cancel button is clicked
    """

    cancelRequested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)

        # Status label
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self._status_label)

        # Current file
        self._current_file_label = QLabel("")
        layout.addWidget(self._current_file_label)

        # File progress
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("Current file:"))
        self._file_progress = QProgressBar()
        self._file_progress.setRange(0, 100)
        self._file_progress.setValue(0)
        file_layout.addWidget(self._file_progress)
        layout.addLayout(file_layout)

        # Overall progress
        overall_layout = QHBoxLayout()
        overall_layout.addWidget(QLabel("Overall:"))
        self._overall_progress = QProgressBar()
        self._overall_progress.setRange(0, 100)
        self._overall_progress.setValue(0)
        overall_layout.addWidget(self._overall_progress)
        layout.addLayout(overall_layout)

        # Cancel button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setEnabled(False)
        button_layout.addWidget(self._cancel_button)
        layout.addLayout(button_layout)

        # Log output (collapsible)
        self._log_group = QGroupBox("Log Output")
        self._log_group.setCheckable(True)
        self._log_group.setChecked(False)
        log_layout = QVBoxLayout(self._log_group)

        self._log_output = QTextEdit()
        self._log_output.setReadOnly(True)
        self._log_output.setMinimumHeight(80)
        self._log_output.setMaximumHeight(200)
        log_layout.addWidget(self._log_output)

        layout.addWidget(self._log_group)
        layout.addStretch()

        # Connect log group toggle
        self._log_group.toggled.connect(self._on_log_toggle)
        self._log_output.setVisible(False)

    def _setup_connections(self) -> None:
        """Connect signals and slots."""
        self._cancel_button.clicked.connect(self.cancelRequested.emit)

    def _on_log_toggle(self, checked: bool) -> None:
        """Handle log group toggle."""
        self._log_output.setVisible(checked)

    def set_status(self, status: str) -> None:
        """Set the status label text."""
        self._status_label.setText(status)

    def set_current_file(self, filename: str) -> None:
        """Set the current file label."""
        self._current_file_label.setText(filename)

    def set_file_progress(self, percent: int) -> None:
        """Set the file progress bar value."""
        self._file_progress.setValue(min(max(percent, 0), 100))

    def set_overall_progress(self, percent: int) -> None:
        """Set the overall progress bar value."""
        self._overall_progress.setValue(min(max(percent, 0), 100))

    def add_log(self, message: str) -> None:
        """Add a message to the log output."""
        self._log_output.append(message)

    def clear_log(self) -> None:
        """Clear the log output."""
        self._log_output.clear()

    def show_log(self) -> None:
        """Expand the log panel so log messages are visible."""
        self._log_group.setChecked(True)

    def set_running(self, running: bool) -> None:
        """Set running state (enables/disables cancel button)."""
        self._cancel_button.setEnabled(running)
        if not running:
            self.set_status("Complete" if self._overall_progress.value() == 100 else "Ready")

    def reset(self) -> None:
        """Reset the panel to initial state."""
        self.set_status("Ready")
        self.set_current_file("")
        self.set_file_progress(0)
        self.set_overall_progress(0)
        self.clear_log()
        self._cancel_button.setEnabled(False)
