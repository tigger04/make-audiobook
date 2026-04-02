# ABOUTME: Tests for ebook metadata extraction from epub and mobi files.
# ABOUTME: Verifies author/title extraction and graceful handling of edge cases.

"""Tests for gui.utils.metadata module."""

import io
import zipfile
from pathlib import Path

import pytest

from gui.utils.metadata import extract_epub_metadata, extract_metadata


def _make_epub(path: Path, *, author: str = "", title: str = "") -> Path:
    """Create a minimal valid epub file for testing.

    Args:
        path: Where to write the epub file.
        author: dc:creator value (omitted if empty).
        title: dc:title value (omitted if empty).

    Returns:
        The path to the created epub file.
    """
    opf_metadata = ""
    if title:
        opf_metadata += f"    <dc:title>{title}</dc:title>\n"
    if author:
        opf_metadata += f"    <dc:creator>{author}</dc:creator>\n"

    opf_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
{opf_metadata}  </metadata>
</package>
"""

    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"
           version="1.0">
  <rootfiles>
    <rootfile full-path="content.opf"
              media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/epub+zip")
        zf.writestr("META-INF/container.xml", container_xml)
        zf.writestr("content.opf", opf_content)

    path.write_bytes(buf.getvalue())
    return path


class TestExtractEpubMetadata:
    """Tests for extract_epub_metadata()."""

    def test_extracts_author_and_title(self, tmp_path):
        """Extract author and title from a well-formed epub."""
        epub = _make_epub(
            tmp_path / "book.epub",
            author="Jane Austen",
            title="Pride and Prejudice",
        )

        result = extract_epub_metadata(epub)

        assert result["author"] == "Jane Austen"
        assert result["title"] == "Pride and Prejudice"

    def test_missing_author_returns_empty_string(self, tmp_path):
        """Missing dc:creator should return empty author."""
        epub = _make_epub(tmp_path / "no_author.epub", title="Some Book")

        result = extract_epub_metadata(epub)

        assert result["author"] == ""
        assert result["title"] == "Some Book"

    def test_missing_title_returns_empty_string(self, tmp_path):
        """Missing dc:title should return empty title."""
        epub = _make_epub(tmp_path / "no_title.epub", author="Author Name")

        result = extract_epub_metadata(epub)

        assert result["author"] == "Author Name"
        assert result["title"] == ""

    def test_missing_both_returns_empty_strings(self, tmp_path):
        """Missing both fields should return empty strings."""
        epub = _make_epub(tmp_path / "empty.epub")

        result = extract_epub_metadata(epub)

        assert result["author"] == ""
        assert result["title"] == ""

    def test_corrupt_epub_returns_empty_dict(self, tmp_path):
        """Non-zip file should return empty metadata gracefully."""
        bad_file = tmp_path / "bad.epub"
        bad_file.write_text("not a zip file")

        result = extract_epub_metadata(bad_file)

        assert result["author"] == ""
        assert result["title"] == ""

    def test_epub_with_nested_opf_path(self, tmp_path):
        """epub with OPF in subdirectory should still be found."""
        opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Nested Book</dc:title>
    <dc:creator>Nested Author</dc:creator>
  </metadata>
</package>
"""
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"
           version="1.0">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf"
              media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""
        epub_path = tmp_path / "nested.epub"
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("mimetype", "application/epub+zip")
            zf.writestr("META-INF/container.xml", container_xml)
            zf.writestr("OEBPS/content.opf", opf_content)
        epub_path.write_bytes(buf.getvalue())

        result = extract_epub_metadata(epub_path)

        assert result["author"] == "Nested Author"
        assert result["title"] == "Nested Book"

    def test_nonexistent_file_returns_empty(self, tmp_path):
        """Non-existent file should return empty metadata."""
        result = extract_epub_metadata(tmp_path / "does_not_exist.epub")

        assert result["author"] == ""
        assert result["title"] == ""

    def test_html_entities_decoded(self, tmp_path):
        """HTML entities in metadata should be decoded."""
        epub = _make_epub(
            tmp_path / "entities.epub",
            author="O&#39;Brien &amp; Co",
            title="The &quot;Great&quot; Book",
        )

        result = extract_epub_metadata(epub)

        assert result["author"] == "O'Brien & Co"
        assert result["title"] == 'The "Great" Book'


class TestExtractMetadata:
    """Tests for the top-level extract_metadata() dispatcher."""

    def test_epub_dispatches_to_epub_extractor(self, tmp_path):
        """epub files should use epub extractor."""
        epub = _make_epub(
            tmp_path / "book.epub",
            author="Test Author",
            title="Test Title",
        )

        result = extract_metadata(epub)

        assert result["author"] == "Test Author"
        assert result["title"] == "Test Title"

    def test_unsupported_format_returns_empty(self, tmp_path):
        """Non-ebook formats should return empty metadata."""
        txt = tmp_path / "plain.txt"
        txt.write_text("just text")

        result = extract_metadata(txt)

        assert result["author"] == ""
        assert result["title"] == ""

    def test_docx_returns_empty(self, tmp_path):
        """docx files (no metadata extraction yet) should return empty."""
        docx = tmp_path / "doc.docx"
        docx.write_bytes(b"not a real docx")

        result = extract_metadata(docx)

        assert result["author"] == ""
        assert result["title"] == ""
