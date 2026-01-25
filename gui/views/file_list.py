# ABOUTME: File list widget for drag-drop file input.
# ABOUTME: Supports adding, removing, and managing files for conversion.

"""FileListWidget for managing input files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, QMimeData, QAbstractListModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListView,
    QFileDialog,
    QLabel,
    QAbstractItemView,
)

logger = logging.getLogger(__name__)

# Supported file extensions for conversion
SUPPORTED_EXTENSIONS = frozenset([".txt", ".epub", ".docx", ".md", ".html", ".pdf"])


class FileListModel(QAbstractListModel):
    """Model for the file list."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._files: list[Path] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._files)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._files):
            return None

        if role == Qt.DisplayRole:
            file_path = self._files[index.row()]
            # Show filename with size
            size_kb = file_path.stat().st_size / 1024
            if size_kb < 1024:
                size_str = f"{size_kb:.1f} KB"
            else:
                size_str = f"{size_kb / 1024:.1f} MB"
            return f"{file_path.name} ({size_str})"

        if role == Qt.ToolTipRole:
            return str(self._files[index.row()])

        return None

    def add_file(self, file_path: Path) -> bool:
        """Add a file to the model."""
        if file_path in self._files:
            return False

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            logger.warning("Unsupported file type: %s", file_path.suffix)
            return False

        self.beginInsertRows(QModelIndex(), len(self._files), len(self._files))
        self._files.append(file_path)
        self.endInsertRows()
        return True

    def remove_file(self, file_path: Path) -> bool:
        """Remove a file from the model."""
        if file_path not in self._files:
            return False

        idx = self._files.index(file_path)
        self.beginRemoveRows(QModelIndex(), idx, idx)
        self._files.remove(file_path)
        self.endRemoveRows()
        return True

    def clear(self) -> None:
        """Remove all files."""
        if not self._files:
            return

        self.beginResetModel()
        self._files.clear()
        self.endResetModel()

    def get_files(self) -> list[Path]:
        """Return list of files."""
        return list(self._files)


class FileListWidget(QWidget):
    """Widget for managing input files with drag-drop support.

    Signals:
        filesChanged: Emitted when files are added or removed
    """

    filesChanged = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)

        # Drop hint label
        self._hint_label = QLabel("Drag files here or click Add Files")
        self._hint_label.setAlignment(Qt.AlignCenter)
        self._hint_label.setStyleSheet("color: gray; padding: 2rem;")

        # File list view
        self._model = FileListModel(self)
        self._list_view = QListView()
        self._list_view.setModel(self._model)
        self._list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._list_view.setDragDropMode(QAbstractItemView.NoDragDrop)

        layout.addWidget(self._hint_label)
        layout.addWidget(self._list_view)

        # Buttons
        button_layout = QHBoxLayout()

        self._add_button = QPushButton("Add Files...")
        self._remove_button = QPushButton("Remove")
        self._clear_button = QPushButton("Clear All")

        button_layout.addWidget(self._add_button)
        button_layout.addWidget(self._remove_button)
        button_layout.addWidget(self._clear_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Update visibility
        self._update_visibility()

    def _setup_connections(self) -> None:
        """Connect signals and slots."""
        self._add_button.clicked.connect(self._on_add_clicked)
        self._remove_button.clicked.connect(self._on_remove_clicked)
        self._clear_button.clicked.connect(self.clear_all)
        self._model.rowsInserted.connect(self._on_files_changed)
        self._model.rowsRemoved.connect(self._on_files_changed)
        self._model.modelReset.connect(self._on_files_changed)

    def _update_visibility(self) -> None:
        """Update visibility of hint vs list."""
        has_files = self._model.rowCount() > 0
        self._hint_label.setVisible(not has_files)
        self._list_view.setVisible(has_files)
        self._remove_button.setEnabled(has_files)
        self._clear_button.setEnabled(has_files)

    def _on_files_changed(self) -> None:
        """Handle file list changes."""
        self._update_visibility()
        self.filesChanged.emit()

    def _on_add_clicked(self) -> None:
        """Handle Add Files button click."""
        extensions = " ".join(f"*{ext}" for ext in SUPPORTED_EXTENSIONS)
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            f"Supported Files ({extensions});;All Files (*)",
        )
        for file_path in files:
            self.add_file(Path(file_path))

    def _on_remove_clicked(self) -> None:
        """Handle Remove button click."""
        selected = self._list_view.selectedIndexes()
        # Remove in reverse order to maintain indices
        for index in sorted(selected, key=lambda i: i.row(), reverse=True):
            file_path = self._model._files[index.row()]
            self._model.remove_file(file_path)

    def add_file(self, file_path: Path) -> bool:
        """Add a file to the list."""
        return self._model.add_file(file_path)

    def add_files(self, file_paths: list[Path]) -> None:
        """Add multiple files to the list."""
        for file_path in file_paths:
            self._model.add_file(file_path)

    def remove_file(self, file_path: Path) -> bool:
        """Remove a file from the list."""
        return self._model.remove_file(file_path)

    def clear_all(self) -> None:
        """Remove all files from the list."""
        self._model.clear()

    def get_files(self) -> list[Path]:
        """Return list of files."""
        return self._model.get_files()

    def file_count(self) -> int:
        """Return number of files in the list."""
        return self._model.rowCount()

    def _handle_drop(self, mime_data: QMimeData) -> None:
        """Process dropped files."""
        if mime_data.hasUrls():
            for url in mime_data.urls():
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.is_file():
                        self.add_file(file_path)

    def dragEnterEvent(self, event) -> None:
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Handle drag move event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """Handle drop event."""
        self._handle_drop(event.mimeData())
        event.acceptProposedAction()
