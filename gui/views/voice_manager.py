# ABOUTME: Widget for managing installed voices.
# ABOUTME: Lists installed voices with delete and browse functionality.

"""VoiceManagerWidget for managing installed voices."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QLabel,
)

from gui.models.voice import Voice
from gui.utils.paths import VOICES_DIR

logger = logging.getLogger(__name__)

# Language flag mapping
LANGUAGE_FLAGS = {
    "en_GB": "\U0001F1EC\U0001F1E7",  # UK flag
    "en_US": "\U0001F1FA\U0001F1F8",  # US flag
    "de_DE": "\U0001F1E9\U0001F1EA",  # German flag
    "fr_FR": "\U0001F1EB\U0001F1F7",  # French flag
    "es_ES": "\U0001F1EA\U0001F1F8",  # Spanish flag
    "it_IT": "\U0001F1EE\U0001F1F9",  # Italian flag
}

# Quality stars
QUALITY_STARS = {
    "high": "\u2B50\u2B50\u2B50",
    "medium": "\u2B50\u2B50",
    "low": "\u2B50",
}


class VoiceManagerWidget(QWidget):
    """Widget for managing installed voices.

    Shows installed voices with language flags and quality indicators.
    Provides buttons for deleting voices and browsing for more.

    Signals:
        browseRequested: Emitted when user wants to browse voices
        voicesChanged: Emitted when voices are added/removed
    """

    browseRequested = Signal()
    voicesChanged = Signal()

    def __init__(
        self,
        voices_dir: Optional[Path] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._voices_dir = voices_dir or VOICES_DIR
        self._voices: list[Voice] = []
        self._setup_ui()
        self._setup_connections()
        self.refresh()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Installed Voices"))
        header_layout.addStretch()
        self._count_label = QLabel("0 voices")
        header_layout.addWidget(self._count_label)
        layout.addLayout(header_layout)

        # Voice list
        self._voice_list = QListWidget()
        self._voice_list.setSelectionMode(QListWidget.ExtendedSelection)
        layout.addWidget(self._voice_list)

        # Buttons
        button_layout = QHBoxLayout()

        self._refresh_button = QPushButton("Refresh")
        self._delete_button = QPushButton("Delete")
        self._browse_button = QPushButton("Browse More Voices...")

        button_layout.addWidget(self._refresh_button)
        button_layout.addWidget(self._delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self._browse_button)

        layout.addLayout(button_layout)

        # Quality hint
        hint = QLabel("\u2B50 Low  \u2B50\u2B50 Medium  \u2B50\u2B50\u2B50 High")
        hint.setStyleSheet("color: gray; font-size: 0.9em;")
        hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint)

    def _setup_connections(self) -> None:
        """Connect signals and slots."""
        self._refresh_button.clicked.connect(self.refresh)
        self._delete_button.clicked.connect(self._on_delete_clicked)
        self._browse_button.clicked.connect(self.browseRequested.emit)
        self._voice_list.itemSelectionChanged.connect(self._update_buttons)

    def _update_buttons(self) -> None:
        """Update button states based on selection."""
        has_selection = len(self._voice_list.selectedItems()) > 0
        self._delete_button.setEnabled(has_selection)

    def refresh(self) -> None:
        """Refresh the voice list from filesystem."""
        self._voices.clear()
        self._voice_list.clear()

        if not self._voices_dir.exists():
            self._count_label.setText("0 voices")
            return

        # Scan for installed voices
        for lang_dir in self._voices_dir.iterdir():
            if not lang_dir.is_dir():
                continue

            for voice_dir in lang_dir.iterdir():
                if not voice_dir.is_dir():
                    continue

                onnx_file = voice_dir / f"{voice_dir.name}.onnx"
                if onnx_file.exists():
                    # Parse voice info from directory name
                    parts = voice_dir.name.split("-")
                    if len(parts) >= 3:
                        language = parts[0]
                        name = parts[1].title()
                        quality = parts[-1]

                        voice = Voice(
                            key=voice_dir.name,
                            name=name,
                            language=language,
                            quality=quality,
                            files={},
                            size_bytes=onnx_file.stat().st_size,
                            installed=True,
                        )
                        self._voices.append(voice)
                        self._add_voice_item(voice)

        self._count_label.setText(f"{len(self._voices)} voice{'s' if len(self._voices) != 1 else ''}")
        self._update_buttons()

    def _add_voice_item(self, voice: Voice) -> None:
        """Add a voice item to the list."""
        flag = LANGUAGE_FLAGS.get(voice.language, "\U0001F310")  # Globe default
        stars = QUALITY_STARS.get(voice.quality, "")

        text = f"{flag} {voice.name} ({voice.language}) {stars}"
        item = QListWidgetItem(text)
        item.setData(Qt.UserRole, voice)
        self._voice_list.addItem(item)

    def _on_delete_clicked(self) -> None:
        """Handle Delete button click."""
        selected = self._voice_list.selectedItems()
        if not selected:
            return

        # Confirm deletion
        count = len(selected)
        msg = f"Delete {count} voice{'s' if count > 1 else ''}?"
        result = QMessageBox.question(
            self,
            "Confirm Deletion",
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if result != QMessageBox.Yes:
            return

        # Delete selected voices
        for item in selected:
            voice = item.data(Qt.UserRole)
            voice_dir = self._voices_dir / voice.language / voice.key

            try:
                if voice_dir.exists():
                    shutil.rmtree(voice_dir)
                    logger.info("Deleted voice: %s", voice.key)
            except OSError as e:
                logger.error("Failed to delete voice %s: %s", voice.key, e)
                QMessageBox.warning(
                    self,
                    "Delete Failed",
                    f"Could not delete {voice.name}: {e}",
                )

        self.refresh()
        self.voicesChanged.emit()

    def get_voices(self) -> list[Voice]:
        """Return list of installed voices."""
        return list(self._voices)
