# ABOUTME: Unit tests for VoiceManagerWidget.
# ABOUTME: Tests voice listing, deletion, refresh, and UI state.

"""Tests for VoiceManagerWidget."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from gui.models.voice import Voice
from gui.views.voice_manager import (
    VoiceManagerWidget,
    LANGUAGE_FLAGS,
    QUALITY_STARS,
)


@pytest.fixture
def voices_dir(tmp_path):
    """Create a temporary voices directory with test voices."""
    # Create en_US/en_US-ryan-high with a fake .onnx file
    voice_path = tmp_path / "en_US" / "en_US-ryan-high"
    voice_path.mkdir(parents=True)
    (voice_path / "en_US-ryan-high.onnx").write_bytes(b"\x00" * 1024)
    (voice_path / "en_US-ryan-high.onnx.json").write_text("{}")

    # Create en_GB/en_GB-alan-medium
    voice_path2 = tmp_path / "en_GB" / "en_GB-alan-medium"
    voice_path2.mkdir(parents=True)
    (voice_path2 / "en_GB-alan-medium.onnx").write_bytes(b"\x00" * 512)
    (voice_path2 / "en_GB-alan-medium.onnx.json").write_text("{}")

    return tmp_path


@pytest.fixture
def empty_voices_dir(tmp_path):
    """Create an empty temporary voices directory."""
    voices = tmp_path / "empty_voices"
    voices.mkdir()
    return voices


@pytest.fixture
def widget(qapp, voices_dir):
    """Create a VoiceManagerWidget with test voices."""
    w = VoiceManagerWidget(voices_dir=voices_dir)
    yield w
    w.close()


@pytest.fixture
def empty_widget(qapp, empty_voices_dir):
    """Create a VoiceManagerWidget with no voices."""
    w = VoiceManagerWidget(voices_dir=empty_voices_dir)
    yield w
    w.close()


class TestVoiceManagerWidget:
    """Tests for VoiceManagerWidget creation and structure."""

    def test_widget_creation(self, widget):
        """Widget should be created successfully."""
        assert widget is not None

    def test_widget_has_voice_list(self, widget):
        """Widget should contain a voice list."""
        assert widget._voice_list is not None

    def test_widget_has_refresh_button(self, widget):
        """Widget should have a Refresh button."""
        assert widget._refresh_button is not None
        assert widget._refresh_button.text() == "Refresh"

    def test_widget_has_delete_button(self, widget):
        """Widget should have a Delete button."""
        assert widget._delete_button is not None
        assert widget._delete_button.text() == "Delete"

    def test_widget_has_browse_button(self, widget):
        """Widget should have a Browse button."""
        assert widget._browse_button is not None
        assert "Browse" in widget._browse_button.text()

    def test_widget_has_count_label(self, widget):
        """Widget should show a voice count label."""
        assert widget._count_label is not None

    def test_widget_has_browse_requested_signal(self, widget):
        """Widget should have browseRequested signal."""
        assert hasattr(widget, "browseRequested")

    def test_widget_has_voices_changed_signal(self, widget):
        """Widget should have voicesChanged signal."""
        assert hasattr(widget, "voicesChanged")


class TestVoiceManagerVoiceListing:
    """Tests for scanning and listing installed voices."""

    def test_lists_installed_voices(self, widget):
        """Widget should list voices found in the voices directory."""
        assert widget._voice_list.count() == 2

    def test_count_label_shows_correct_count(self, widget):
        """Count label should reflect the number of installed voices."""
        assert widget._count_label.text() == "2 voices"

    def test_count_label_singular_form(self, qapp, tmp_path):
        """Count label should use singular when only one voice."""
        voice_path = tmp_path / "en_US" / "en_US-ryan-high"
        voice_path.mkdir(parents=True)
        (voice_path / "en_US-ryan-high.onnx").write_bytes(b"\x00" * 1024)

        w = VoiceManagerWidget(voices_dir=tmp_path)
        assert w._count_label.text() == "1 voice"
        w.close()

    def test_empty_dir_shows_zero_voices(self, empty_widget):
        """Widget should show 0 voices for an empty directory."""
        assert empty_widget._voice_list.count() == 0
        assert empty_widget._count_label.text() == "0 voices"

    def test_nonexistent_dir_shows_zero_voices(self, qapp, tmp_path):
        """Widget should handle nonexistent voices directory."""
        w = VoiceManagerWidget(voices_dir=tmp_path / "nonexistent")
        assert w._voice_list.count() == 0
        assert w._count_label.text() == "0 voices"
        w.close()

    def test_voice_item_stores_voice_data(self, widget):
        """Each list item should store a Voice object in UserRole."""
        item = widget._voice_list.item(0)
        voice = item.data(Qt.UserRole)
        assert isinstance(voice, Voice)

    def test_voice_item_shows_language_flag(self, widget):
        """Voice items should display language flags."""
        texts = [widget._voice_list.item(i).text() for i in range(widget._voice_list.count())]
        # At least one should have a known flag
        has_flag = any(
            flag in text
            for text in texts
            for flag in LANGUAGE_FLAGS.values()
        )
        assert has_flag

    def test_voice_item_shows_quality_stars(self, widget):
        """Voice items should display quality stars."""
        texts = [widget._voice_list.item(i).text() for i in range(widget._voice_list.count())]
        has_stars = any(
            stars in text
            for text in texts
            for stars in QUALITY_STARS.values()
        )
        assert has_stars

    def test_get_voices_returns_voice_list(self, widget):
        """get_voices() should return a list of Voice objects."""
        voices = widget.get_voices()
        assert len(voices) == 2
        assert all(isinstance(v, Voice) for v in voices)

    def test_get_voices_returns_copy(self, widget):
        """get_voices() should return a copy, not the internal list."""
        voices = widget.get_voices()
        voices.clear()
        assert len(widget.get_voices()) == 2

    def test_voices_marked_as_installed(self, widget):
        """All listed voices should have installed=True."""
        voices = widget.get_voices()
        assert all(v.installed for v in voices)


class TestVoiceManagerRefresh:
    """Tests for the refresh functionality."""

    def test_refresh_rescans_directory(self, widget, voices_dir):
        """Refresh should rescan the voices directory."""
        # Add a new voice
        voice_path = voices_dir / "de_DE" / "de_DE-thorsten-high"
        voice_path.mkdir(parents=True)
        (voice_path / "de_DE-thorsten-high.onnx").write_bytes(b"\x00" * 256)

        widget.refresh()
        assert widget._voice_list.count() == 3

    def test_refresh_updates_count_label(self, widget, voices_dir):
        """Refresh should update the count label."""
        # Add a new voice
        voice_path = voices_dir / "fr_FR" / "fr_FR-siwis-medium"
        voice_path.mkdir(parents=True)
        (voice_path / "fr_FR-siwis-medium.onnx").write_bytes(b"\x00" * 256)

        widget.refresh()
        assert widget._count_label.text() == "3 voices"


class TestVoiceManagerButtonStates:
    """Tests for button enable/disable states."""

    def test_delete_button_disabled_when_no_selection(self, widget):
        """Delete button should be disabled with no selection."""
        widget._voice_list.clearSelection()
        widget._update_buttons()
        assert not widget._delete_button.isEnabled()

    def test_delete_button_enabled_when_selected(self, widget):
        """Delete button should be enabled when a voice is selected."""
        widget._voice_list.setCurrentRow(0)
        assert widget._delete_button.isEnabled()


class TestVoiceManagerDelete:
    """Tests for voice deletion."""

    def test_delete_removes_voice_directory(self, widget, voices_dir, monkeypatch):
        """Deleting a voice should remove its directory."""
        # Select the first voice
        widget._voice_list.setCurrentRow(0)
        voice = widget._voice_list.item(0).data(Qt.UserRole)

        # Monkeypatch QMessageBox to auto-confirm
        monkeypatch.setattr(
            "gui.views.voice_manager.QMessageBox.question",
            staticmethod(lambda *args, **kwargs: QMessageBox.Yes),
        )

        voice_dir = voices_dir / voice.language / voice.key
        assert voice_dir.exists()

        widget._on_delete_clicked()

        assert not voice_dir.exists()

    def test_delete_refreshes_list(self, widget, voices_dir, monkeypatch):
        """After deletion, the voice list should be refreshed."""
        widget._voice_list.setCurrentRow(0)

        monkeypatch.setattr(
            "gui.views.voice_manager.QMessageBox.question",
            staticmethod(lambda *args, **kwargs: QMessageBox.Yes),
        )

        widget._on_delete_clicked()
        assert widget._voice_list.count() == 1

    def test_delete_emits_voices_changed(self, widget, voices_dir, monkeypatch, qtbot):
        """Deletion should emit the voicesChanged signal."""
        widget._voice_list.setCurrentRow(0)

        monkeypatch.setattr(
            "gui.views.voice_manager.QMessageBox.question",
            staticmethod(lambda *args, **kwargs: QMessageBox.Yes),
        )

        with qtbot.waitSignal(widget.voicesChanged, timeout=1000):
            widget._on_delete_clicked()

    def test_delete_cancelled_preserves_voices(self, widget, monkeypatch):
        """Cancelling deletion should preserve all voices."""
        widget._voice_list.setCurrentRow(0)

        monkeypatch.setattr(
            "gui.views.voice_manager.QMessageBox.question",
            staticmethod(lambda *args, **kwargs: QMessageBox.No),
        )

        widget._on_delete_clicked()
        assert widget._voice_list.count() == 2

    def test_delete_with_no_selection_does_nothing(self, widget):
        """Delete with no selection should do nothing."""
        widget._voice_list.clearSelection()
        widget._on_delete_clicked()
        assert widget._voice_list.count() == 2


class TestVoiceManagerBrowse:
    """Tests for the browse button."""

    def test_browse_button_emits_signal(self, widget, qtbot):
        """Clicking Browse should emit browseRequested signal."""
        with qtbot.waitSignal(widget.browseRequested, timeout=1000):
            widget._browse_button.click()


class TestLanguageFlags:
    """Tests for the language flag mapping."""

    def test_en_gb_has_flag(self):
        """en_GB should have a UK flag."""
        assert "en_GB" in LANGUAGE_FLAGS

    def test_en_us_has_flag(self):
        """en_US should have a US flag."""
        assert "en_US" in LANGUAGE_FLAGS

    def test_unknown_language_gets_globe(self, widget, voices_dir):
        """Unknown languages should get a globe emoji."""
        voice_path = voices_dir / "xx_XX" / "xx_XX-test-medium"
        voice_path.mkdir(parents=True)
        (voice_path / "xx_XX-test-medium.onnx").write_bytes(b"\x00" * 256)

        widget.refresh()
        texts = [widget._voice_list.item(i).text() for i in range(widget._voice_list.count())]
        # The globe emoji should appear for the unknown language
        assert any("\U0001F310" in t for t in texts)


class TestQualityStars:
    """Tests for the quality stars mapping."""

    def test_high_has_three_stars(self):
        """High quality should show three stars."""
        assert len(QUALITY_STARS["high"]) >= 3

    def test_medium_has_two_stars(self):
        """Medium quality should show two stars."""
        assert len(QUALITY_STARS["medium"]) >= 2

    def test_low_has_one_star(self):
        """Low quality should show one star."""
        assert len(QUALITY_STARS["low"]) >= 1
