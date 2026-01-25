# ABOUTME: Dialog for browsing and downloading voices from HuggingFace.
# ABOUTME: Provides filtering by language/quality and multi-select download.

"""VoiceBrowserDialog for browsing available voices."""

from __future__ import annotations

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal, QSortFilterProxyModel, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableView,
    QLineEdit,
    QComboBox,
    QLabel,
    QHeaderView,
    QAbstractItemView,
)

from gui.models.voice import Voice, VoiceCatalog

logger = logging.getLogger(__name__)


class VoiceTableModel(QAbstractTableModel):
    """Table model for displaying voices."""

    COLUMNS = ["Name", "Language", "Quality", "Size", "Status"]

    def __init__(self, catalog: VoiceCatalog, parent=None):
        super().__init__(parent)
        self._catalog = catalog
        self._voices = catalog.voices

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._voices)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._voices):
            return None

        voice = self._voices[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:  # Name
                return voice.name
            elif col == 1:  # Language
                return voice.language
            elif col == 2:  # Quality
                return voice.quality.title()
            elif col == 3:  # Size
                mb = voice.size_bytes / (1024 * 1024)
                return f"{mb:.1f} MB"
            elif col == 4:  # Status
                return "Installed" if voice.installed else ""

        if role == Qt.UserRole:
            return voice

        return None

    def get_voice(self, row: int) -> Optional[Voice]:
        """Get voice at row."""
        if 0 <= row < len(self._voices):
            return self._voices[row]
        return None


class VoiceFilterProxyModel(QSortFilterProxyModel):
    """Proxy model for filtering voices."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language_filter = ""
        self._quality_filter = ""
        self._search_filter = ""

    def set_language_filter(self, language: str) -> None:
        self._language_filter = language
        self.invalidateFilter()  # noqa: PySide6-deprecated - invalidateRowsFilter not in all versions

    def set_quality_filter(self, quality: str) -> None:
        self._quality_filter = quality
        self.invalidateFilter()  # noqa: PySide6-deprecated - invalidateRowsFilter not in all versions

    def set_search_filter(self, text: str) -> None:
        self._search_filter = text.lower()
        self.invalidateFilter()  # noqa: PySide6-deprecated - invalidateRowsFilter not in all versions

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        voice = model.get_voice(source_row)
        if voice is None:
            return False

        if self._language_filter and voice.language != self._language_filter:
            return False

        if self._quality_filter and voice.quality != self._quality_filter:
            return False

        if self._search_filter and self._search_filter not in voice.name.lower():
            return False

        return True


class VoiceBrowserDialog(QDialog):
    """Dialog for browsing and downloading voices.

    Signals:
        downloadRequested(list[Voice]): Emitted when user requests download
    """

    downloadRequested = Signal(list)

    def __init__(
        self,
        catalog: VoiceCatalog,
        parent: Optional[QDialog] = None,
    ):
        super().__init__(parent)
        self._catalog = catalog
        self._setup_ui()
        self._setup_connections()
        self._populate_filters()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        self.setWindowTitle("Browse Voices")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)

        # Filter bar
        filter_layout = QHBoxLayout()

        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search by name...")

        self._language_filter = QComboBox()
        self._language_filter.setMinimumWidth(100)

        self._quality_filter = QComboBox()
        self._quality_filter.setMinimumWidth(100)

        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self._search_box)
        filter_layout.addWidget(QLabel("Language:"))
        filter_layout.addWidget(self._language_filter)
        filter_layout.addWidget(QLabel("Quality:"))
        filter_layout.addWidget(self._quality_filter)
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        # Table view
        self._table_model = VoiceTableModel(self._catalog)
        self._proxy_model = VoiceFilterProxyModel()
        self._proxy_model.setSourceModel(self._table_model)

        self._table_view = QTableView()
        self._table_view.setModel(self._proxy_model)
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)

        layout.addWidget(self._table_view)

        # Buttons
        button_layout = QHBoxLayout()

        self._download_button = QPushButton("Download Selected")
        self._close_button = QPushButton("Close")

        button_layout.addStretch()
        button_layout.addWidget(self._download_button)
        button_layout.addWidget(self._close_button)

        layout.addLayout(button_layout)

    def _setup_connections(self) -> None:
        """Connect signals and slots."""
        self._search_box.textChanged.connect(self._on_search_changed)
        self._language_filter.currentTextChanged.connect(self._on_language_changed)
        self._quality_filter.currentTextChanged.connect(self._on_quality_changed)
        self._download_button.clicked.connect(self._on_download_clicked)
        self._close_button.clicked.connect(self.accept)

    def _populate_filters(self) -> None:
        """Populate filter dropdowns."""
        # Language filter
        self._language_filter.addItem("All", "")
        for lang in sorted(self._catalog.get_languages()):
            self._language_filter.addItem(lang, lang)

        # Quality filter
        self._quality_filter.addItem("All", "")
        for quality in ["high", "medium", "low"]:
            if quality in self._catalog.get_qualities():
                self._quality_filter.addItem(quality.title(), quality)

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        self._proxy_model.set_search_filter(text)

    def _on_language_changed(self, text: str) -> None:
        """Handle language filter change."""
        data = self._language_filter.currentData()
        self._proxy_model.set_language_filter(data or "")

    def _on_quality_changed(self, text: str) -> None:
        """Handle quality filter change."""
        data = self._quality_filter.currentData()
        self._proxy_model.set_quality_filter(data or "")

    def _on_download_clicked(self) -> None:
        """Handle Download button click."""
        voices = self.get_selected_voices()
        if voices:
            self.downloadRequested.emit(voices)

    def get_selected_voices(self) -> list[Voice]:
        """Return list of selected voices."""
        voices = []
        for index in self._table_view.selectionModel().selectedRows():
            source_index = self._proxy_model.mapToSource(index)
            voice = self._table_model.get_voice(source_index.row())
            if voice:
                voices.append(voice)
        return voices

    def _apply_language_filter(self, language: str) -> None:
        """Apply language filter (for testing)."""
        self._proxy_model.set_language_filter(language)

    def _apply_quality_filter(self, quality: str) -> None:
        """Apply quality filter (for testing)."""
        self._proxy_model.set_quality_filter(quality)

    def _apply_search_filter(self, text: str) -> None:
        """Apply search filter (for testing)."""
        self._proxy_model.set_search_filter(text)

    def _clear_filters(self) -> None:
        """Clear all filters (for testing)."""
        self._proxy_model.set_language_filter("")
        self._proxy_model.set_quality_filter("")
        self._proxy_model.set_search_filter("")

    def _get_visible_voice_count(self) -> int:
        """Get count of visible voices (for testing)."""
        return self._proxy_model.rowCount()

    def _get_voice_at_row(self, row: int) -> Optional[Voice]:
        """Get voice at visible row (for testing)."""
        proxy_index = self._proxy_model.index(row, 0)
        source_index = self._proxy_model.mapToSource(proxy_index)
        return self._table_model.get_voice(source_index.row())

    def _get_status_at_row(self, row: int) -> str:
        """Get status text at row (for testing)."""
        proxy_index = self._proxy_model.index(row, 4)  # Status column
        return self._proxy_model.data(proxy_index, Qt.DisplayRole) or ""

    def _get_size_text_at_row(self, row: int) -> str:
        """Get size text at row (for testing)."""
        proxy_index = self._proxy_model.index(row, 3)  # Size column
        return self._proxy_model.data(proxy_index, Qt.DisplayRole) or ""

    def _get_language_filter_items(self) -> list[str]:
        """Get all language filter items (for testing)."""
        return [self._language_filter.itemText(i) for i in range(self._language_filter.count())]

    def _get_quality_filter_items(self) -> list[str]:
        """Get all quality filter items (for testing)."""
        return [self._quality_filter.itemText(i) for i in range(self._quality_filter.count())]
