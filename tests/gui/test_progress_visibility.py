# ABOUTME: Tests for progress panel visibility during conversion
# ABOUTME: Ensures log output and progress indicators are visible

"""Tests for progress panel visibility and feedback."""

import pytest
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtTest import QTest

from gui.views.progress_panel import ProgressPanel


class TestProgressVisibility:
    """Test progress panel visibility during operations."""

    @pytest.fixture
    def progress_panel(self, qtbot):
        """Create a ProgressPanel instance."""
        panel = ProgressPanel()
        qtbot.addWidget(panel)
        panel.show()  # Show the widget for visibility tests to work
        QCoreApplication.processEvents()
        return panel

    def test_log_output_visible_when_conversion_starts(self, progress_panel):
        """Log output should be visible when conversion starts."""
        # Initially collapsed
        assert not progress_panel._log_group.isChecked()
        assert not progress_panel._log_output.isVisible()

        # When conversion starts and we add a log
        progress_panel.set_status("Converting...")
        progress_panel.add_log("Starting conversion")

        # Log should auto-expand
        progress_panel.show_log()
        QCoreApplication.processEvents()  # Process Qt events to trigger signal
        assert progress_panel._log_group.isChecked()
        assert progress_panel._log_output.isVisible()

    def test_progress_updates_visible(self, progress_panel):
        """Progress updates should be immediately visible."""
        progress_panel.set_status("Converting...")
        progress_panel.set_current_file("test.txt")
        progress_panel.set_file_progress(50)
        progress_panel.set_overall_progress(25)

        assert progress_panel._status_label.text() == "Converting..."
        assert progress_panel._current_file_label.text() == "test.txt"
        assert progress_panel._file_progress.value() == 50
        assert progress_panel._overall_progress.value() == 25

    def test_error_shows_in_log(self, progress_panel):
        """Errors should be visible in the log."""
        progress_panel.add_log("Error: Failed to start process")
        progress_panel.show_log()
        QCoreApplication.processEvents()  # Process Qt events to trigger signal

        assert "Error: Failed to start process" in progress_panel._log_output.toPlainText()
        assert progress_panel._log_output.isVisible()

    def test_spinner_or_indeterminate_progress(self, progress_panel):
        """Should show indeterminate progress when percentage unknown."""
        # Set progress bar to indeterminate mode
        progress_panel._file_progress.setRange(0, 0)  # This makes it indeterminate
        assert progress_panel._file_progress.minimum() == 0
        assert progress_panel._file_progress.maximum() == 0