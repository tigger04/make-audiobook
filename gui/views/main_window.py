# ABOUTME: Main application window for make-audiobook GUI.
# ABOUTME: Assembles all widgets into tabs with menus and status bar.

"""MainWindow for make-audiobook GUI."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QMenuBar,
    QMenu,
    QStatusBar,
    QFileDialog,
    QMessageBox,
    QSplitter,
)

from gui.models.conversion_job import ConversionJob, JobStatus
from gui.utils.paths import VOICES_DIR, CONFIG_FILE
from gui.utils.config import load_config, save_config
from gui.views.file_list import FileListWidget, SUPPORTED_EXTENSIONS
from gui.views.settings_panel import SettingsPanel
from gui.views.progress_panel import ProgressPanel
from gui.views.voice_manager import VoiceManagerWidget
from gui.views.voice_browser import VoiceBrowserDialog
from gui.workers.catalog_worker import CatalogWorker
from gui.workers.conversion_worker import ConversionWorker
from gui.workers.download_worker import DownloadWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window.

    Contains tabbed interface with:
    - Convert tab: File list, settings, and progress
    - Voices tab: Voice management
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._config = load_config()
        self._conversion_worker: Optional[ConversionWorker] = None
        self._conversion_thread: Optional[QThread] = None

        self._setup_ui()
        self._setup_menus()
        self._setup_status_bar()
        self._setup_connections()
        self._apply_config()

    def _setup_ui(self) -> None:
        """Set up the main window UI."""
        self.setWindowTitle("make-audiobook")
        self.setMinimumSize(700, 500)

        # Central widget with tabs
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self._tab_widget = QTabWidget()
        layout.addWidget(self._tab_widget)

        # Convert tab
        self._setup_convert_tab()

        # Voices tab
        self._setup_voices_tab()

    def _setup_convert_tab(self) -> None:
        """Set up the Convert tab."""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Left side: file list
        left_layout = QVBoxLayout()
        self._file_list = FileListWidget()
        left_layout.addWidget(self._file_list)

        # Convert button
        self._convert_button = QPushButton("Convert to Audiobook")
        self._convert_button.setEnabled(False)
        left_layout.addWidget(self._convert_button)

        layout.addLayout(left_layout, 2)

        # Right side: settings and progress
        right_layout = QVBoxLayout()

        # Get installed voices for settings panel
        installed_voices = self._scan_installed_voices()
        self._settings_panel = SettingsPanel(installed_voices=installed_voices)
        right_layout.addWidget(self._settings_panel)

        self._progress_panel = ProgressPanel()
        right_layout.addWidget(self._progress_panel)

        layout.addLayout(right_layout, 1)

        self._tab_widget.addTab(tab, "Convert")

    def _setup_voices_tab(self) -> None:
        """Set up the Voices tab."""
        self._voice_manager = VoiceManagerWidget()
        self._tab_widget.addTab(self._voice_manager, "Voices")

    def _setup_menus(self) -> None:
        """Set up the menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        open_action = file_menu.addAction("Open Files...")
        open_action.triggered.connect(self._on_open_files)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Tools menu
        tools_menu = menu_bar.addMenu("Tools")

        update_catalog_action = tools_menu.addAction("Update Voice Catalog")
        update_catalog_action.triggered.connect(self._on_update_catalog)

        # Help menu
        help_menu = menu_bar.addMenu("Help")

        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self._on_about)

    def _setup_status_bar(self) -> None:
        """Set up the status bar."""
        status_bar = self.statusBar()
        voice_count = len(self._scan_installed_voices())
        status_bar.showMessage(f"{voice_count} voices installed")

    def _setup_connections(self) -> None:
        """Connect signals and slots."""
        self._file_list.filesChanged.connect(self._on_files_changed)
        self._convert_button.clicked.connect(self._on_convert_clicked)
        self._progress_panel.cancelRequested.connect(self._on_cancel_clicked)
        self._voice_manager.browseRequested.connect(self._on_browse_voices)
        self._voice_manager.voicesChanged.connect(self._on_voices_changed)

    def _apply_config(self) -> None:
        """Apply saved configuration."""
        # Restore window geometry
        geometry = self._config.get("window_geometry")
        if geometry:
            self.setGeometry(
                geometry.get("x", 100),
                geometry.get("y", 100),
                geometry.get("width", 800),
                geometry.get("height", 600),
            )

        # Restore settings
        if self._config.get("length_scale"):
            self._settings_panel.set_length_scale(self._config["length_scale"])

    def _save_config(self) -> None:
        """Save current configuration."""
        self._config["window_geometry"] = {
            "x": self.x(),
            "y": self.y(),
            "width": self.width(),
            "height": self.height(),
        }
        self._config["length_scale"] = self._settings_panel.get_length_scale()
        self._config["last_voice"] = self._settings_panel.get_selected_voice()

        save_config(self._config)

    def _scan_installed_voices(self) -> list:
        """Scan for installed voices."""
        from gui.models.voice import Voice

        voices = []
        if not VOICES_DIR.exists():
            return voices

        for lang_dir in VOICES_DIR.iterdir():
            if not lang_dir.is_dir():
                continue
            for voice_dir in lang_dir.iterdir():
                if not voice_dir.is_dir():
                    continue
                onnx_file = voice_dir / f"{voice_dir.name}.onnx"
                if onnx_file.exists():
                    parts = voice_dir.name.split("-")
                    if len(parts) >= 3:
                        voice = Voice(
                            key=voice_dir.name,
                            name=parts[1].title(),
                            language=parts[0],
                            quality=parts[-1],
                            files={},
                            size_bytes=onnx_file.stat().st_size,
                            installed=True,
                        )
                        voices.append(voice)

        return voices

    def _on_files_changed(self) -> None:
        """Handle file list changes."""
        has_files = self._file_list.file_count() > 0
        self._convert_button.setEnabled(has_files)

    def _on_convert_clicked(self) -> None:
        """Handle Convert button click."""
        files = self._file_list.get_files()
        if not files:
            return

        # Create conversion job
        job = ConversionJob(
            files=files,
            voice_key=self._settings_panel.get_selected_voice(),
            random_voice=self._settings_panel.is_random_mode(),
            random_filter=self._settings_panel.get_random_filter(),
            length_scale=self._settings_panel.get_length_scale(),
            author=self._settings_panel.get_author(),
            title=self._settings_panel.get_title(),
        )

        # Start conversion
        self._start_conversion(job)

    def _start_conversion(self, job: ConversionJob) -> None:
        """Start a conversion job."""
        self._conversion_worker = ConversionWorker(job)
        self._conversion_thread = QThread()

        self._conversion_worker.moveToThread(self._conversion_thread)
        self._conversion_thread.started.connect(self._conversion_worker.start)
        self._conversion_worker.progress.connect(self._on_conversion_progress)
        self._conversion_worker.log.connect(self._progress_panel.add_log)
        self._conversion_worker.finished.connect(self._on_conversion_finished)

        self._progress_panel.reset()
        self._progress_panel.set_status("Converting...")
        self._progress_panel.set_running(True)
        self._convert_button.setEnabled(False)

        self._conversion_thread.start()

    def _on_conversion_progress(self, filename: str, percent: int) -> None:
        """Handle conversion progress update."""
        self._progress_panel.set_current_file(filename)
        self._progress_panel.set_file_progress(percent)

    def _on_conversion_finished(self, filename: str, success: bool) -> None:
        """Handle conversion completion."""
        self._progress_panel.set_running(False)
        self._convert_button.setEnabled(True)

        if self._conversion_thread:
            self._conversion_thread.quit()
            self._conversion_thread.wait()
            self._conversion_thread = None

        if success:
            self._progress_panel.set_status("Conversion complete!")
            self._progress_panel.set_overall_progress(100)
        else:
            self._progress_panel.set_status("Conversion failed")
            QMessageBox.warning(self, "Conversion Failed", f"Failed to convert {filename}")

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click."""
        if self._conversion_worker:
            self._conversion_worker.cancel()
            self._progress_panel.set_status("Cancelled")

    def _on_open_files(self) -> None:
        """Handle File > Open menu action."""
        extensions = " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            f"Supported Files ({extensions});;All Files (*)",
        )
        for file_path in files:
            self._file_list.add_file(Path(file_path))

    def _on_update_catalog(self) -> None:
        """Handle Tools > Update Voice Catalog menu action."""
        self.statusBar().showMessage("Updating voice catalog...")
        worker = CatalogWorker(force_refresh=True)
        worker.catalogReady.connect(lambda c: self.statusBar().showMessage("Voice catalog updated"))
        worker.error.connect(lambda e: QMessageBox.warning(self, "Error", f"Failed to update: {e}"))
        worker.run()

    def _on_browse_voices(self) -> None:
        """Handle Browse Voices button click."""
        # Fetch catalog
        worker = CatalogWorker()
        worker.catalogReady.connect(self._show_voice_browser)
        worker.error.connect(lambda e: QMessageBox.warning(self, "Error", f"Failed to load voices: {e}"))
        worker.run()

    def _show_voice_browser(self, catalog) -> None:
        """Show the voice browser dialog."""
        # Update installed status
        catalog.update_installed_status(VOICES_DIR)

        dialog = VoiceBrowserDialog(catalog, self)
        dialog.downloadRequested.connect(self._on_download_voices)
        dialog.exec()

    def _on_download_voices(self, voices) -> None:
        """Handle voice download request."""
        for voice in voices:
            worker = DownloadWorker(voice)
            worker.finished.connect(lambda s: self._on_voice_downloaded(s, voice))
            worker.run()

    def _on_voice_downloaded(self, success: bool, voice) -> None:
        """Handle voice download completion."""
        if success:
            self._voice_manager.refresh()
            self._on_voices_changed()
            self.statusBar().showMessage(f"Downloaded {voice.name}")
        else:
            QMessageBox.warning(self, "Download Failed", f"Failed to download {voice.name}")

    def _on_voices_changed(self) -> None:
        """Handle changes to installed voices."""
        voices = self._scan_installed_voices()
        self._settings_panel.refresh_voices(voices)
        self.statusBar().showMessage(f"{len(voices)} voices installed")

    def _on_about(self) -> None:
        """Show About dialog."""
        QMessageBox.about(
            self,
            "About make-audiobook",
            "make-audiobook\n\n"
            "Convert documents to audiobooks using Piper TTS.\n\n"
            "Local, open-source, and private.\n\n"
            "MIT License - Tadhg Paul",
        )

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self._save_config()
        super().closeEvent(event)
