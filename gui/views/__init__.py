# ABOUTME: UI view components for the make-audiobook GUI.
# ABOUTME: Contains widgets for file list, voice browser, settings, and progress.

"""UI view components for make-audiobook GUI."""

from gui.views.file_list import FileListWidget, SUPPORTED_EXTENSIONS
from gui.views.voice_browser import VoiceBrowserDialog
from gui.views.voice_manager import VoiceManagerWidget
from gui.views.settings_panel import SettingsPanel
from gui.views.progress_panel import ProgressPanel
from gui.views.main_window import MainWindow

__all__ = [
    "FileListWidget",
    "SUPPORTED_EXTENSIONS",
    "VoiceBrowserDialog",
    "VoiceManagerWidget",
    "SettingsPanel",
    "ProgressPanel",
    "MainWindow",
]
