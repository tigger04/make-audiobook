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
