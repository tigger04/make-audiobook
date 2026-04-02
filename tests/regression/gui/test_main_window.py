# ABOUTME: Tests for MainWindow that integrates all GUI components.
# ABOUTME: Verifies window creation, tab layout, and application flow.

"""Tests for MainWindow."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from gui.views.main_window import MainWindow


class TestMainWindow:
    """Tests for MainWindow."""

    def test_window_creation(self, qapp):
        """Test MainWindow can be created."""
        window = MainWindow()
        assert window is not None
        window.close()

    def test_window_has_title(self, qapp):
        """Test MainWindow has a title."""
        window = MainWindow()
        assert "make-audiobook" in window.windowTitle().lower()
        window.close()

    def test_window_has_tabs(self, qapp):
        """Test MainWindow has tab widget."""
        window = MainWindow()
        assert window._tab_widget is not None
        window.close()

    def test_window_has_convert_tab(self, qapp):
        """Test MainWindow has Convert tab."""
        window = MainWindow()
        assert window._tab_widget.count() >= 1
        assert "convert" in window._tab_widget.tabText(0).lower()
        window.close()

    def test_window_has_voices_tab(self, qapp):
        """Test MainWindow has Voices tab."""
        window = MainWindow()
        assert window._tab_widget.count() >= 2
        assert "voice" in window._tab_widget.tabText(1).lower()
        window.close()

    def test_window_has_menu_bar(self, qapp):
        """Test MainWindow has menu bar."""
        window = MainWindow()
        menu_bar = window.menuBar()
        assert menu_bar is not None
        window.close()

    def test_window_has_file_menu(self, qapp):
        """Test MainWindow has File menu."""
        window = MainWindow()
        menus = [a.text() for a in window.menuBar().actions()]
        assert any("file" in m.lower() for m in menus)
        window.close()

    def test_window_has_status_bar(self, qapp):
        """Test MainWindow has status bar."""
        window = MainWindow()
        assert window.statusBar() is not None
        window.close()

    def test_convert_tab_has_file_list(self, qapp):
        """Test Convert tab contains FileListWidget."""
        window = MainWindow()
        assert window._file_list is not None
        window.close()

    def test_convert_tab_has_settings(self, qapp):
        """Test Convert tab contains SettingsPanel."""
        window = MainWindow()
        assert window._settings_panel is not None
        window.close()

    def test_convert_tab_has_progress(self, qapp):
        """Test Convert tab contains ProgressPanel."""
        window = MainWindow()
        assert window._progress_panel is not None
        window.close()

    def test_convert_tab_has_convert_button(self, qapp):
        """Test Convert tab has Convert button."""
        window = MainWindow()
        assert window._convert_button is not None
        window.close()

    def test_voices_tab_has_voice_manager(self, qapp):
        """Test Voices tab contains VoiceManagerWidget."""
        window = MainWindow()
        assert window._voice_manager is not None
        window.close()


class TestMainWindowConvertFlow:
    """Tests for conversion flow in MainWindow."""

    def test_convert_button_disabled_initially(self, qapp):
        """Test Convert button disabled when no files."""
        window = MainWindow()
        assert not window._convert_button.isEnabled()
        window.close()

    def test_convert_button_enabled_with_files(self, qapp, tmp_path):
        """Test Convert button enabled when files added."""
        window = MainWindow()

        # Add a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        window._file_list.add_file(test_file)

        assert window._convert_button.isEnabled()
        window.close()


class TestMainWindowMenu:
    """Tests for MainWindow menu functionality."""

    def test_file_menu_has_open(self, qapp):
        """Test File menu has Open action."""
        window = MainWindow()
        file_menu = None
        for action in window.menuBar().actions():
            if "file" in action.text().lower():
                file_menu = action.menu()
                break

        assert file_menu is not None
        actions = [a.text() for a in file_menu.actions()]
        assert any("open" in a.lower() for a in actions)
        window.close()

    def test_file_menu_has_exit(self, qapp):
        """Test File menu has Exit action."""
        window = MainWindow()
        file_menu = None
        for action in window.menuBar().actions():
            if "file" in action.text().lower():
                file_menu = action.menu()
                break

        assert file_menu is not None
        actions = [a.text() for a in file_menu.actions()]
        assert any("exit" in a.lower() or "quit" in a.lower() for a in actions)
        window.close()


class TestMainWindowMetadataPopulation:
    """Tests for ebook metadata auto-population in MainWindow."""

    def _make_epub(self, path, *, author="", title=""):
        """Create a minimal epub file for testing."""
        import io
        import zipfile

        opf_metadata = ""
        if title:
            opf_metadata += f"    <dc:title>{title}</dc:title>\n"
        if author:
            opf_metadata += f"    <dc:creator>{author}</dc:creator>\n"

        opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
{opf_metadata}  </metadata>
</package>"""

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile full-path="content.opf"
              media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("content.opf", opf_content)
        path.write_bytes(buf.getvalue())
        return path

    def test_epub_metadata_populates_author_and_title(self, qapp, tmp_path):
        """Adding an epub should pre-populate author and title fields."""
        window = MainWindow()
        epub = self._make_epub(
            tmp_path / "book.epub",
            author="Jane Austen",
            title="Pride and Prejudice",
        )

        window._file_list.add_file(epub)

        assert window._settings_panel.get_author() == "Jane Austen"
        assert window._settings_panel.get_title() == "Pride and Prejudice"
        window.close()

    def test_txt_file_does_not_populate_metadata(self, qapp, tmp_path):
        """Adding a txt file should not change metadata fields."""
        window = MainWindow()
        txt = tmp_path / "test.txt"
        txt.write_text("content")

        window._file_list.add_file(txt)

        assert window._settings_panel.get_author() == ""
        assert window._settings_panel.get_title() == ""
        window.close()

    def test_metadata_does_not_overwrite_user_input(self, qapp, tmp_path):
        """Metadata extraction should not overwrite user-entered values."""
        window = MainWindow()
        window._settings_panel._author_field.setText("Custom Author")
        window._settings_panel._title_field.setText("Custom Title")

        epub = self._make_epub(
            tmp_path / "book.epub",
            author="Epub Author",
            title="Epub Title",
        )
        window._file_list.add_file(epub)

        assert window._settings_panel.get_author() == "Custom Author"
        assert window._settings_panel.get_title() == "Custom Title"
        window.close()

    def test_first_ebook_metadata_used_for_multiple_files(self, qapp, tmp_path):
        """When multiple files added, metadata from first ebook is used."""
        window = MainWindow()
        txt = tmp_path / "intro.txt"
        txt.write_text("intro")
        epub = self._make_epub(
            tmp_path / "book.epub",
            author="First Author",
            title="First Book",
        )

        window._file_list.add_file(txt)
        window._file_list.add_file(epub)

        assert window._settings_panel.get_author() == "First Author"
        assert window._settings_panel.get_title() == "First Book"
        window.close()


class TestMainWindowConfiguration:
    """Tests for MainWindow configuration persistence."""

    def test_window_saves_geometry(self, qapp, tmp_path):
        """Test window saves geometry on close."""
        config_file = tmp_path / "settings.json"

        with patch("gui.views.main_window.CONFIG_FILE", config_file):
            window = MainWindow()
            window.resize(800, 600)
            window.close()

        # Config should be saved (tested via the config module)

    def test_window_has_minimum_size(self, qapp):
        """Test window has reasonable minimum size."""
        window = MainWindow()
        min_size = window.minimumSize()
        assert min_size.width() >= 600
        assert min_size.height() >= 400
        window.close()
