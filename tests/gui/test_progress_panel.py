# ABOUTME: Unit tests for ProgressPanel widget.
# ABOUTME: Tests progress display, status updates, log output, and cancel.

"""Tests for ProgressPanel."""

import pytest

from gui.views.progress_panel import ProgressPanel


@pytest.fixture
def panel(qapp):
    """Create a ProgressPanel instance."""
    p = ProgressPanel()
    yield p
    p.close()


class TestProgressPanelCreation:
    """Tests for ProgressPanel widget structure."""

    def test_panel_creation(self, panel):
        """Panel should be created successfully."""
        assert panel is not None

    def test_panel_has_status_label(self, panel):
        """Panel should have a status label."""
        assert panel._status_label is not None

    def test_panel_has_current_file_label(self, panel):
        """Panel should have a current file label."""
        assert panel._current_file_label is not None

    def test_panel_has_file_progress_bar(self, panel):
        """Panel should have a per-file progress bar."""
        assert panel._file_progress is not None

    def test_panel_has_overall_progress_bar(self, panel):
        """Panel should have an overall progress bar."""
        assert panel._overall_progress is not None

    def test_panel_has_cancel_button(self, panel):
        """Panel should have a cancel button."""
        assert panel._cancel_button is not None
        assert panel._cancel_button.text() == "Cancel"

    def test_panel_has_log_output(self, panel):
        """Panel should have a log output area."""
        assert panel._log_output is not None

    def test_panel_has_cancel_requested_signal(self, panel):
        """Panel should have cancelRequested signal."""
        assert hasattr(panel, "cancelRequested")


class TestProgressPanelInitialState:
    """Tests for the initial state of the panel."""

    def test_initial_status_is_ready(self, panel):
        """Initial status should be 'Ready'."""
        assert panel._status_label.text() == "Ready"

    def test_initial_file_label_is_empty(self, panel):
        """Initial current file label should be empty."""
        assert panel._current_file_label.text() == ""

    def test_initial_file_progress_is_zero(self, panel):
        """Initial file progress should be 0."""
        assert panel._file_progress.value() == 0

    def test_initial_overall_progress_is_zero(self, panel):
        """Initial overall progress should be 0."""
        assert panel._overall_progress.value() == 0

    def test_cancel_button_initially_disabled(self, panel):
        """Cancel button should be disabled initially."""
        assert not panel._cancel_button.isEnabled()

    def test_log_output_initially_empty(self, panel):
        """Log output should be empty initially."""
        assert panel._log_output.toPlainText() == ""

    def test_log_output_is_read_only(self, panel):
        """Log output should be read-only."""
        assert panel._log_output.isReadOnly()

    def test_log_group_initially_collapsed(self, panel):
        """Log group should be collapsed (unchecked) initially."""
        assert not panel._log_group.isChecked()


class TestProgressPanelSetStatus:
    """Tests for set_status()."""

    def test_set_status_updates_label(self, panel):
        """set_status() should update the status label."""
        panel.set_status("Converting...")
        assert panel._status_label.text() == "Converting..."

    def test_set_status_with_empty_string(self, panel):
        """set_status() should accept empty string."""
        panel.set_status("")
        assert panel._status_label.text() == ""


class TestProgressPanelSetCurrentFile:
    """Tests for set_current_file()."""

    def test_set_current_file_updates_label(self, panel):
        """set_current_file() should update the file label."""
        panel.set_current_file("chapter01.epub")
        assert panel._current_file_label.text() == "chapter01.epub"


class TestProgressPanelFileProgress:
    """Tests for set_file_progress()."""

    def test_set_file_progress(self, panel):
        """set_file_progress() should update the progress bar."""
        panel.set_file_progress(50)
        assert panel._file_progress.value() == 50

    def test_file_progress_clamped_at_100(self, panel):
        """File progress should be clamped to 100 maximum."""
        panel.set_file_progress(150)
        assert panel._file_progress.value() == 100

    def test_file_progress_clamped_at_zero(self, panel):
        """File progress should be clamped to 0 minimum."""
        panel.set_file_progress(-10)
        assert panel._file_progress.value() == 0


class TestProgressPanelOverallProgress:
    """Tests for set_overall_progress()."""

    def test_set_overall_progress(self, panel):
        """set_overall_progress() should update the progress bar."""
        panel.set_overall_progress(75)
        assert panel._overall_progress.value() == 75

    def test_overall_progress_clamped_at_100(self, panel):
        """Overall progress should be clamped to 100 maximum."""
        panel.set_overall_progress(200)
        assert panel._overall_progress.value() == 100

    def test_overall_progress_clamped_at_zero(self, panel):
        """Overall progress should be clamped to 0 minimum."""
        panel.set_overall_progress(-5)
        assert panel._overall_progress.value() == 0


class TestProgressPanelLogOutput:
    """Tests for log output functionality."""

    def test_add_log_appends_message(self, panel):
        """add_log() should append a message to the log."""
        panel.add_log("Starting conversion")
        assert "Starting conversion" in panel._log_output.toPlainText()

    def test_add_log_multiple_messages(self, panel):
        """add_log() should accumulate messages."""
        panel.add_log("Line 1")
        panel.add_log("Line 2")
        text = panel._log_output.toPlainText()
        assert "Line 1" in text
        assert "Line 2" in text

    def test_clear_log(self, panel):
        """clear_log() should remove all log content."""
        panel.add_log("Some message")
        panel.clear_log()
        assert panel._log_output.toPlainText() == ""

    def test_log_toggle_visibility(self, panel):
        """Toggling the log group should show/hide the log output."""
        panel._log_group.setChecked(True)
        assert not panel._log_output.isHidden()

        panel._log_group.setChecked(False)
        assert panel._log_output.isHidden()


class TestProgressPanelRunningState:
    """Tests for set_running()."""

    def test_set_running_true_enables_cancel(self, panel):
        """set_running(True) should enable the cancel button."""
        panel.set_running(True)
        assert panel._cancel_button.isEnabled()

    def test_set_running_false_disables_cancel(self, panel):
        """set_running(False) should disable the cancel button."""
        panel.set_running(True)
        panel.set_running(False)
        assert not panel._cancel_button.isEnabled()

    def test_set_running_false_shows_complete_at_100(self, panel):
        """set_running(False) should show 'Complete' when at 100%."""
        panel.set_overall_progress(100)
        panel.set_running(False)
        assert panel._status_label.text() == "Complete"

    def test_set_running_false_shows_ready_when_not_100(self, panel):
        """set_running(False) should show 'Ready' when not at 100%."""
        panel.set_overall_progress(50)
        panel.set_running(False)
        assert panel._status_label.text() == "Ready"


class TestProgressPanelReset:
    """Tests for reset()."""

    def test_reset_clears_status(self, panel):
        """reset() should set status to 'Ready'."""
        panel.set_status("Converting...")
        panel.reset()
        assert panel._status_label.text() == "Ready"

    def test_reset_clears_current_file(self, panel):
        """reset() should clear the current file label."""
        panel.set_current_file("test.epub")
        panel.reset()
        assert panel._current_file_label.text() == ""

    def test_reset_zeroes_file_progress(self, panel):
        """reset() should set file progress to 0."""
        panel.set_file_progress(50)
        panel.reset()
        assert panel._file_progress.value() == 0

    def test_reset_zeroes_overall_progress(self, panel):
        """reset() should set overall progress to 0."""
        panel.set_overall_progress(75)
        panel.reset()
        assert panel._overall_progress.value() == 0

    def test_reset_clears_log(self, panel):
        """reset() should clear the log output."""
        panel.add_log("Some log message")
        panel.reset()
        assert panel._log_output.toPlainText() == ""

    def test_reset_disables_cancel(self, panel):
        """reset() should disable the cancel button."""
        panel.set_running(True)
        panel.reset()
        assert not panel._cancel_button.isEnabled()


class TestProgressPanelCancelSignal:
    """Tests for cancel button signal."""

    def test_cancel_button_emits_signal(self, panel, qtbot):
        """Clicking Cancel should emit cancelRequested signal."""
        panel.set_running(True)
        with qtbot.waitSignal(panel.cancelRequested, timeout=1000):
            panel._cancel_button.click()
