# ABOUTME: Tests for Kokoro TTS GUI integration behaviour.
# ABOUTME: Ensures proper UI state, voice switching, and engine selection for Kokoro.

"""Tests for Kokoro GUI behaviour."""

import pytest
from PySide6.QtCore import QCoreApplication

from gui.models.voice import Voice
from gui.views.settings_panel import SettingsPanel


class TestKokoroEngineSelection:
    """Test Kokoro engine selection in the settings panel."""

    @pytest.fixture
    def settings_panel(self, qtbot):
        """Create a SettingsPanel instance with test Piper voices."""
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

    def test_engine_selector_has_kokoro_option(self, settings_panel):
        """Engine selector should include Kokoro as an option."""
        items = [
            settings_panel._engine_selector.itemText(i)
            for i in range(settings_panel._engine_selector.count())
        ]
        assert any("Kokoro" in item for item in items)

    def test_set_engine_kokoro(self, settings_panel):
        """set_engine('kokoro') should select Kokoro in the dropdown."""
        settings_panel.set_engine("kokoro")
        QCoreApplication.processEvents()
        assert settings_panel.get_selected_engine() == "kokoro"

    def test_set_engine_piper(self, settings_panel):
        """set_engine('piper') should select Piper in the dropdown."""
        settings_panel.set_engine("kokoro")
        settings_panel.set_engine("piper")
        QCoreApplication.processEvents()
        assert settings_panel.get_selected_engine() == "piper"

    def test_set_engine_whisperspeech(self, settings_panel):
        """set_engine('whisperspeech') should select WhisperSpeech."""
        settings_panel.set_engine("whisperspeech")
        QCoreApplication.processEvents()
        assert settings_panel.get_selected_engine() == "whisperspeech"


class TestKokoroVoiceSwitching:
    """Test voice list switching when Kokoro is selected."""

    @pytest.fixture
    def piper_voices(self):
        """Sample Piper voices."""
        return [
            Voice(
                key="en_US-ryan-high",
                name="Ryan",
                language="en_US",
                quality="high",
                files={},
                size_bytes=1000,
                installed=True,
            ),
            Voice(
                key="en_GB-alba-medium",
                name="Alba",
                language="en_GB",
                quality="medium",
                files={},
                size_bytes=1000,
                installed=True,
            ),
        ]

    @pytest.fixture
    def settings_panel(self, qtbot, piper_voices):
        """Create a SettingsPanel with Piper voices."""
        panel = SettingsPanel(installed_voices=piper_voices)
        qtbot.addWidget(panel)
        panel.show()
        QCoreApplication.processEvents()
        return panel

    def test_kokoro_voices_shown_initially(self, settings_panel):
        """Kokoro voices should be listed by default (Kokoro is the default engine)."""
        assert settings_panel._voice_selector.count() == 26

    def test_kokoro_voices_shown_when_selected(self, settings_panel):
        """Kokoro voices should be listed when Kokoro engine is selected."""
        settings_panel.set_engine("kokoro")
        QCoreApplication.processEvents()

        # Kokoro has 26 built-in voices
        assert settings_panel._voice_selector.count() == 26

    def test_switching_back_to_piper_restores_piper_voices(self, settings_panel):
        """Switching back to Piper should show Piper voices again."""
        settings_panel.set_engine("kokoro")
        QCoreApplication.processEvents()
        assert settings_panel._voice_selector.count() == 26

        settings_panel.set_engine("piper")
        QCoreApplication.processEvents()
        assert settings_panel._voice_selector.count() == 2

    def test_kokoro_voice_keys_are_correct(self, settings_panel):
        """Kokoro voice dropdown should contain correct voice keys."""
        settings_panel.set_engine("kokoro")
        QCoreApplication.processEvents()

        # Check a few known voice keys
        voice_keys = [
            settings_panel._voice_selector.itemData(i)
            for i in range(settings_panel._voice_selector.count())
        ]
        assert "af_heart" in voice_keys
        assert "am_adam" in voice_keys
        assert "bf_alice" in voice_keys


class TestKokoroUIState:
    """Test UI state when Kokoro engine is selected."""

    @pytest.fixture
    def settings_panel(self, qtbot):
        """Create a SettingsPanel."""
        panel = SettingsPanel(installed_voices=[
            Voice(
                key="en_US-ryan-high",
                name="Ryan",
                language="en_US",
                quality="high",
                files={},
                size_bytes=1000,
                installed=True,
            ),
        ])
        qtbot.addWidget(panel)
        panel.show()
        QCoreApplication.processEvents()
        return panel

    def test_random_checkbox_disabled_for_kokoro(self, settings_panel):
        """Random voice checkbox should be disabled for Kokoro."""
        settings_panel.set_engine("kokoro")
        QCoreApplication.processEvents()
        assert not settings_panel._random_checkbox.isEnabled()

    def test_voice_selector_enabled_for_kokoro(self, settings_panel):
        """Voice selector should be enabled for Kokoro (to choose a voice)."""
        settings_panel.set_engine("kokoro")
        QCoreApplication.processEvents()
        assert settings_panel._voice_selector.isEnabled()

    def test_speed_slider_enabled_for_kokoro(self, settings_panel):
        """Speed slider should remain enabled for Kokoro."""
        settings_panel.set_engine("kokoro")
        QCoreApplication.processEvents()
        assert settings_panel._speed_slider.isEnabled()

    def test_random_filter_hidden_for_kokoro(self, settings_panel):
        """Random filter should be hidden for Kokoro."""
        # Switch to Piper first, then enable random
        settings_panel.set_engine("piper")
        QCoreApplication.processEvents()
        settings_panel._random_checkbox.setChecked(True)
        QCoreApplication.processEvents()

        # Switch to Kokoro
        settings_panel.set_engine("kokoro")
        QCoreApplication.processEvents()

        assert not settings_panel._random_filter.isVisible()
        assert not settings_panel._random_filter_label.isVisible()
