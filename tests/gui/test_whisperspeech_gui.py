# ABOUTME: Tests for WhisperSpeech GUI integration behavior
# ABOUTME: Ensures proper UI state when switching between TTS engines

"""Tests for WhisperSpeech GUI behavior."""

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QTest

from gui.models.voice import Voice
from gui.views.settings_panel import SettingsPanel


class TestWhisperSpeechGUIBehavior:
    """Test WhisperSpeech GUI integration behavior."""

    @pytest.fixture
    def settings_panel(self, qtbot):
        """Create a SettingsPanel instance with test voices."""
        test_voices = [
            Voice(
                key="en_US-ryan-high",
                name="Ryan",
                language="en_US",
                quality="high",
                files={},
                size_bytes=1000,
                installed=True,
            )
        ]
        panel = SettingsPanel(installed_voices=test_voices)
        qtbot.addWidget(panel)
        panel.show()
        QCoreApplication.processEvents()
        return panel

    def test_piper_voice_controls_disabled_when_whisperspeech_selected(self, settings_panel):
        """When WhisperSpeech is selected, Piper voice controls should be disabled."""
        # Initially Piper is selected, voice controls should be enabled
        assert settings_panel.get_selected_engine() == "piper"
        assert settings_panel._voice_selector.isEnabled()
        assert settings_panel._random_checkbox.isEnabled()

        # Switch to WhisperSpeech
        settings_panel._engine_selector.setCurrentIndex(2)  # WhisperSpeech is index 2
        QCoreApplication.processEvents()

        # Voice controls should now be disabled
        assert settings_panel.get_selected_engine() == "whisperspeech"
        assert not settings_panel._voice_selector.isEnabled()
        assert not settings_panel._random_checkbox.isEnabled()
        assert not settings_panel._random_filter.isEnabled()
        assert not settings_panel._random_filter_label.isEnabled()

    def test_speed_control_remains_enabled_for_whisperspeech(self, settings_panel):
        """Speed control should remain enabled for WhisperSpeech."""
        # Switch to WhisperSpeech
        settings_panel._engine_selector.setCurrentIndex(1)
        QCoreApplication.processEvents()

        # Speed controls should still be enabled
        assert settings_panel._speed_slider.isEnabled()
        assert settings_panel._speed_display.isVisible()

    def test_switching_back_to_piper_reenables_controls(self, settings_panel):
        """Switching back to Piper should re-enable voice controls."""
        # Switch to WhisperSpeech
        settings_panel._engine_selector.setCurrentIndex(1)
        QCoreApplication.processEvents()

        # Switch back to Piper
        settings_panel._engine_selector.setCurrentIndex(0)
        QCoreApplication.processEvents()

        # Voice controls should be enabled again
        assert settings_panel.get_selected_engine() == "piper"
        assert settings_panel._voice_selector.isEnabled()
        assert settings_panel._random_checkbox.isEnabled()

    def test_random_filter_respects_engine_selection(self, settings_panel):
        """Random filter should only be visible for Piper engine."""
        # Enable random mode with Piper
        settings_panel._random_checkbox.setChecked(True)
        QCoreApplication.processEvents()

        # Filter should be visible with Piper
        assert settings_panel._random_filter.isVisible()
        assert settings_panel._random_filter_label.isVisible()

        # Switch to WhisperSpeech
        settings_panel._engine_selector.setCurrentIndex(1)
        QCoreApplication.processEvents()

        # Filter should be hidden even though random is checked
        assert not settings_panel._random_filter.isVisible()
        assert not settings_panel._random_filter_label.isVisible()