# ABOUTME: Tests for VoiceBrowserDialog that browses available voices.
# ABOUTME: Verifies filtering, selection, and download functionality.

"""Tests for VoiceBrowserDialog."""

import pytest
from unittest.mock import MagicMock


from gui.views.voice_browser import VoiceBrowserDialog
from gui.models.voice import Voice, VoiceCatalog


# qapp fixture is provided by conftest.py


@pytest.fixture
def sample_catalog():
    """Create a sample VoiceCatalog for testing."""
    voices = [
        Voice(
            key="en_US-ryan-high",
            name="Ryan",
            language="en_US",
            quality="high",
            files={},
            size_bytes=60000000,
        ),
        Voice(
            key="en_US-amy-medium",
            name="Amy",
            language="en_US",
            quality="medium",
            files={},
            size_bytes=20000000,
        ),
        Voice(
            key="en_GB-alba-medium",
            name="Alba",
            language="en_GB",
            quality="medium",
            files={},
            size_bytes=18000000,
        ),
        Voice(
            key="de_DE-thorsten-high",
            name="Thorsten",
            language="de_DE",
            quality="high",
            files={},
            size_bytes=55000000,
            installed=True,
        ),
    ]
    return VoiceCatalog(voices=voices)


@pytest.fixture
def dialog(qapp, sample_catalog):
    """Create a VoiceBrowserDialog for testing."""
    d = VoiceBrowserDialog(catalog=sample_catalog)
    yield d
    d.close()


class TestVoiceBrowserDialog:
    """Tests for VoiceBrowserDialog."""

    def test_dialog_creation(self, dialog):
        """Test VoiceBrowserDialog can be created."""
        assert dialog is not None

    def test_dialog_has_table_view(self, dialog):
        """Test dialog has a table view for voices."""
        assert dialog._table_view is not None

    def test_dialog_has_search_box(self, dialog):
        """Test dialog has a search filter box."""
        assert dialog._search_box is not None

    def test_dialog_has_language_filter(self, dialog):
        """Test dialog has language filter dropdown."""
        assert dialog._language_filter is not None

    def test_dialog_has_quality_filter(self, dialog):
        """Test dialog has quality filter dropdown."""
        assert dialog._quality_filter is not None

    def test_dialog_has_download_button(self, dialog):
        """Test dialog has download button."""
        assert dialog._download_button is not None

    def test_table_shows_all_voices(self, dialog, sample_catalog):
        """Test table displays all voices from catalog."""
        model = dialog._table_model
        assert model.rowCount() == len(sample_catalog.voices)

    def test_filter_by_language(self, dialog):
        """Test filtering voices by language."""
        dialog._apply_language_filter("en_US")
        visible_count = dialog._get_visible_voice_count()
        assert visible_count == 2

    def test_filter_by_quality(self, dialog):
        """Test filtering voices by quality."""
        dialog._apply_quality_filter("high")
        visible_count = dialog._get_visible_voice_count()
        assert visible_count == 2

    def test_search_filter(self, dialog):
        """Test search box filters by name."""
        dialog._apply_search_filter("ryan")
        visible_count = dialog._get_visible_voice_count()
        assert visible_count == 1

    def test_clear_filters(self, dialog, sample_catalog):
        """Test clearing all filters."""
        dialog._apply_language_filter("en_US")
        dialog._clear_filters()
        visible_count = dialog._get_visible_voice_count()
        assert visible_count == len(sample_catalog.voices)

    def test_get_selected_voices(self, dialog):
        """Test getting selected voices."""
        # Select first voice
        dialog._table_view.selectRow(0)
        selected = dialog.get_selected_voices()
        assert len(selected) == 1

    def test_download_requested_signal(self, dialog, qapp):
        """Test downloadRequested signal is emitted."""
        received = []
        dialog.downloadRequested.connect(lambda v: received.append(v))

        # Select a voice and click download
        dialog._table_view.selectRow(0)
        dialog._on_download_clicked()

        assert len(received) == 1

    def test_shows_installed_status(self, dialog, sample_catalog):
        """Test installed voices show status indicator."""
        # Thorsten is installed, should be indicated
        model = dialog._table_model
        # Find the installed voice row and check status
        for row in range(model.rowCount()):
            voice = dialog._get_voice_at_row(row)
            if voice.installed:
                status = dialog._get_status_at_row(row)
                assert status == "Installed"

    def test_size_formatted_as_mb(self, dialog):
        """Test file sizes are formatted as MB."""
        model = dialog._table_model
        # Check size column has MB format
        size_text = dialog._get_size_text_at_row(0)
        assert "MB" in size_text or "MiB" in size_text


class TestVoiceBrowserLanguageFilter:
    """Tests for language filter functionality."""

    def test_language_filter_has_all_option(self, dialog):
        """Test language filter includes 'All' option."""
        filter_items = dialog._get_language_filter_items()
        assert "All" in filter_items or "" in filter_items

    def test_language_filter_lists_all_languages(self, dialog, sample_catalog):
        """Test language filter shows all available languages."""
        filter_items = dialog._get_language_filter_items()
        languages = sample_catalog.get_languages()
        for lang in languages:
            assert any(lang in item for item in filter_items)


class TestVoiceBrowserQualityFilter:
    """Tests for quality filter functionality."""

    def test_quality_filter_has_all_option(self, dialog):
        """Test quality filter includes 'All' option."""
        filter_items = dialog._get_quality_filter_items()
        assert "All" in filter_items or "" in filter_items

    def test_quality_filter_lists_all_qualities(self, dialog, sample_catalog):
        """Test quality filter shows all quality levels."""
        filter_items = dialog._get_quality_filter_items()
        for quality in ["high", "medium", "low"]:
            if quality in sample_catalog.get_qualities():
                assert any(quality in item.lower() for item in filter_items)
