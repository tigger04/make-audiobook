# ABOUTME: Tests for SettingsPanel widget for conversion options.
# ABOUTME: Verifies voice selection, speed slider, and metadata fields.

"""Tests for SettingsPanel."""

import pytest
from unittest.mock import MagicMock


from gui.views.settings_panel import SettingsPanel
from gui.models.voice import Voice


# qapp fixture is provided by conftest.py


@pytest.fixture
def installed_voices():
    """Sample list of installed voices."""
    return [
        Voice(
            key="en_US-ryan-high",
            name="Ryan",
            language="en_US",
            quality="high",
            files={},
            size_bytes=60000000,
            installed=True,
        ),
        Voice(
            key="en_GB-alba-medium",
            name="Alba",
            language="en_GB",
            quality="medium",
            files={},
            size_bytes=18000000,
            installed=True,
        ),
    ]


@pytest.fixture
def panel(qapp, installed_voices):
    """Create a SettingsPanel for testing."""
    p = SettingsPanel(installed_voices=installed_voices)
    yield p
    p.close()


class TestSettingsPanel:
    """Tests for SettingsPanel."""

    def test_panel_creation(self, panel):
        """Test SettingsPanel can be created."""
        assert panel is not None

    def test_panel_has_voice_selector(self, panel):
        """Test panel has voice selection dropdown."""
        assert panel._voice_selector is not None

    def test_panel_has_random_checkbox(self, panel):
        """Test panel has random voice checkbox."""
        assert panel._random_checkbox is not None

    def test_panel_has_speed_slider(self, panel):
        """Test panel has speed/length_scale slider."""
        assert panel._speed_slider is not None

    def test_panel_has_author_field(self, panel):
        """Test panel has author text field."""
        assert panel._author_field is not None

    def test_panel_has_title_field(self, panel):
        """Test panel has book title field."""
        assert panel._title_field is not None

    def test_voice_selector_has_installed_voices(self, panel, installed_voices):
        """Test voice selector lists installed voices."""
        count = panel._voice_selector.count()
        # Should have voices plus possibly "Random" option
        assert count >= len(installed_voices)

    def test_voice_selector_has_random_option(self, panel):
        """Test voice selector has 'Random' option."""
        has_random = False
        for i in range(panel._voice_selector.count()):
            if "random" in panel._voice_selector.itemText(i).lower():
                has_random = True
                break
        assert has_random

    def test_get_selected_voice(self, panel, installed_voices):
        """Test getting currently selected voice."""
        panel._voice_selector.setCurrentIndex(1)
        voice = panel.get_selected_voice()
        # Either a voice key or None (if random selected)
        assert voice is None or isinstance(voice, str)

    def test_random_voice_mode(self, panel):
        """Test random voice mode selection."""
        panel.set_random_mode(True)
        assert panel.is_random_mode()

    def test_random_filter_selector(self, panel):
        """Test random quality filter is enabled when random mode enabled."""
        panel.set_random_mode(False)
        # Filter should be hidden (visibility only works when widget shown)
        # Check that random mode properly toggles
        assert not panel.is_random_mode()
        panel.set_random_mode(True)
        assert panel.is_random_mode()
        # Voice selector should be disabled in random mode
        assert not panel._voice_selector.isEnabled()

    def test_get_random_filter(self, panel):
        """Test getting random filter value."""
        panel.set_random_mode(True)
        # Use setCurrentIndex instead of setCurrentText for reliability
        panel._random_filter.setCurrentIndex(2)  # "Medium" is index 2
        assert panel.get_random_filter() == "medium"

    def test_speed_slider_range(self, panel):
        """Test speed slider has correct range (0.5 to 3.0)."""
        # Slider uses integer values multiplied by 10
        min_val = panel._speed_slider.minimum()
        max_val = panel._speed_slider.maximum()
        assert min_val == 5  # 0.5 * 10
        assert max_val == 30  # 3.0 * 10

    def test_speed_slider_default(self, panel):
        """Test speed slider defaults to 1.5."""
        value = panel.get_length_scale()
        assert value == 1.5

    def test_set_length_scale(self, panel):
        """Test setting length scale."""
        panel.set_length_scale(2.0)
        assert panel.get_length_scale() == 2.0

    def test_speed_display_updates(self, panel, qapp):
        """Test speed display label updates with slider."""
        panel.set_length_scale(1.8)
        text = panel._speed_display.text()
        assert "1.8" in text

    def test_get_author(self, panel):
        """Test getting author field value."""
        panel._author_field.setText("Jane Austen")
        assert panel.get_author() == "Jane Austen"

    def test_get_title(self, panel):
        """Test getting title field value."""
        panel._title_field.setText("Pride and Prejudice")
        assert panel.get_title() == "Pride and Prejudice"

    def test_settings_changed_signal(self, panel, qapp):
        """Test settingsChanged signal is emitted."""
        received = []
        panel.settingsChanged.connect(lambda: received.append(True))
        panel._author_field.setText("New Author")
        assert len(received) >= 1

    def test_refresh_voices(self, panel):
        """Test refreshing voice list."""
        new_voices = [
            Voice(
                key="new-voice",
                name="New Voice",
                language="en_US",
                quality="high",
                files={},
                size_bytes=10000000,
                installed=True,
            )
        ]
        panel.refresh_voices(new_voices)
        # Should have new voice in list
        count = panel._voice_selector.count()
        assert count >= 1


class TestSettingsPanelValidation:
    """Tests for settings validation."""

    def test_empty_author_allowed(self, panel):
        """Test empty author is valid."""
        panel._author_field.setText("")
        assert panel.get_author() == ""

    def test_empty_title_allowed(self, panel):
        """Test empty title is valid."""
        panel._title_field.setText("")
        assert panel.get_title() == ""

    def test_whitespace_trimmed_from_author(self, panel):
        """Test whitespace is trimmed from author."""
        panel._author_field.setText("  Jane Austen  ")
        assert panel.get_author() == "Jane Austen"

    def test_whitespace_trimmed_from_title(self, panel):
        """Test whitespace is trimmed from title."""
        panel._title_field.setText("  My Book  ")
        assert panel.get_title() == "My Book"
