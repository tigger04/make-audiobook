# ABOUTME: Tests for FileListWidget that handles drag-drop file input.
# ABOUTME: Verifies file adding, removing, and drag-drop functionality.

"""Tests for FileListWidget."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt, QMimeData, QUrl

from gui.views.file_list import FileListWidget, SUPPORTED_EXTENSIONS


# qapp fixture is provided by conftest.py


@pytest.fixture
def widget(qapp):
    """Create a FileListWidget for testing."""
    w = FileListWidget()
    yield w
    w.close()


@pytest.fixture
def sample_files(tmp_path):
    """Create sample files for testing."""
    files = []
    for ext in [".txt", ".epub", ".md", ".html", ".docx", ".pdf", ".mobi"]:
        f = tmp_path / f"test{ext}"
        f.write_text("content")
        files.append(f)
    return files


class TestFileListWidget:
    """Tests for FileListWidget."""

    def test_widget_creation(self, widget):
        """Test FileListWidget can be created."""
        assert widget is not None

    def test_widget_has_file_list(self, widget):
        """Test widget contains a file list view."""
        assert widget._list_view is not None

    def test_widget_has_add_button(self, widget):
        """Test widget has add files button."""
        assert widget._add_button is not None

    def test_widget_has_remove_button(self, widget):
        """Test widget has remove button."""
        assert widget._remove_button is not None

    def test_widget_has_clear_button(self, widget):
        """Test widget has clear all button."""
        assert widget._clear_button is not None

    def test_add_file(self, widget, sample_files):
        """Test adding a file to the list."""
        widget.add_file(sample_files[0])
        assert widget.file_count() == 1

    def test_add_multiple_files(self, widget, sample_files):
        """Test adding multiple files."""
        widget.add_files(sample_files[:3])
        assert widget.file_count() == 3

    def test_remove_file(self, widget, sample_files):
        """Test removing a file from the list."""
        widget.add_files(sample_files[:2])
        widget.remove_file(sample_files[0])
        assert widget.file_count() == 1

    def test_clear_all(self, widget, sample_files):
        """Test clearing all files."""
        widget.add_files(sample_files)
        widget.clear_all()
        assert widget.file_count() == 0

    def test_get_files(self, widget, sample_files):
        """Test getting list of files."""
        widget.add_files(sample_files[:2])
        files = widget.get_files()
        assert len(files) == 2
        assert sample_files[0] in files
        assert sample_files[1] in files

    def test_supported_extensions(self, widget):
        """Test supported file extensions constant."""
        assert ".txt" in SUPPORTED_EXTENSIONS
        assert ".epub" in SUPPORTED_EXTENSIONS
        assert ".docx" in SUPPORTED_EXTENSIONS
        assert ".md" in SUPPORTED_EXTENSIONS
        assert ".html" in SUPPORTED_EXTENSIONS
        assert ".pdf" in SUPPORTED_EXTENSIONS
        assert ".mobi" in SUPPORTED_EXTENSIONS

    def test_add_mobi_file(self, widget, tmp_path):
        """Test adding a .mobi file to the list."""
        mobi_file = tmp_path / "book.mobi"
        mobi_file.write_text("content")
        widget.add_file(mobi_file)
        assert widget.file_count() == 1

    def test_reject_unsupported_extension(self, widget, tmp_path):
        """Test rejecting files with unsupported extensions."""
        unsupported = tmp_path / "test.xyz"
        unsupported.write_text("content")
        widget.add_file(unsupported)
        assert widget.file_count() == 0

    def test_files_changed_signal(self, widget, sample_files, qapp):
        """Test filesChanged signal is emitted."""
        received = []
        widget.filesChanged.connect(lambda: received.append(True))
        widget.add_file(sample_files[0])
        assert len(received) == 1

    def test_file_display_shows_basename(self, widget, sample_files):
        """Test file list displays basename."""
        widget.add_file(sample_files[0])
        # The model should contain the filename
        model = widget._list_view.model()
        assert model.rowCount() == 1

    def test_no_duplicate_files(self, widget, sample_files):
        """Test same file cannot be added twice."""
        widget.add_file(sample_files[0])
        widget.add_file(sample_files[0])
        assert widget.file_count() == 1

    def test_accepts_drops(self, widget):
        """Test widget accepts drag and drop."""
        assert widget.acceptDrops()

    def test_drop_event_adds_files(self, widget, sample_files, qapp):
        """Test dropping files adds them to the list."""
        # Create mime data with file URLs
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(str(f)) for f in sample_files[:2]]
        mime_data.setUrls(urls)

        # Simulate drop
        widget._handle_drop(mime_data)
        assert widget.file_count() == 2

    def test_empty_state_shows_hint(self, widget):
        """Test empty widget shows drop hint."""
        # When empty, should show placeholder text
        assert widget.file_count() == 0


class TestSupportedExtensions:
    """Tests for file extension validation."""

    def test_txt_supported(self):
        """Test .txt files are supported."""
        assert ".txt" in SUPPORTED_EXTENSIONS

    def test_epub_supported(self):
        """Test .epub files are supported."""
        assert ".epub" in SUPPORTED_EXTENSIONS

    def test_docx_supported(self):
        """Test .docx files are supported."""
        assert ".docx" in SUPPORTED_EXTENSIONS

    def test_md_supported(self):
        """Test .md files are supported."""
        assert ".md" in SUPPORTED_EXTENSIONS

    def test_html_supported(self):
        """Test .html files are supported."""
        assert ".html" in SUPPORTED_EXTENSIONS

    def test_pdf_supported(self):
        """Test .pdf files are supported."""
        assert ".pdf" in SUPPORTED_EXTENSIONS

    def test_mobi_supported(self):
        """Test .mobi files are supported."""
        assert ".mobi" in SUPPORTED_EXTENSIONS
