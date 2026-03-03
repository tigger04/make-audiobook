# ABOUTME: Extract metadata (author, title) from ebook files.
# ABOUTME: Supports epub (via zipfile+XML) and mobi (via ebook-meta CLI).

"""Ebook metadata extraction for pre-populating ID3 tags."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Dublin Core namespace used in OPF metadata
_DC_NS = "http://purl.org/dc/elements/1.1/"
_CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"

# Formats that support metadata extraction
_EBOOK_EXTENSIONS = frozenset([".epub", ".mobi"])


def _empty_metadata() -> dict[str, str]:
    """Return an empty metadata dict."""
    return {"author": "", "title": ""}


def extract_epub_metadata(path: Path) -> dict[str, str]:
    """Extract author and title from an epub file.

    Parses META-INF/container.xml to locate the OPF file, then extracts
    dc:creator and dc:title from the OPF metadata section.

    Args:
        path: Path to the epub file.

    Returns:
        Dict with 'author' and 'title' keys (empty strings if not found).
    """
    if not path.exists():
        return _empty_metadata()

    try:
        with zipfile.ZipFile(path, "r") as zf:
            # Find OPF path from container.xml
            container = zf.read("META-INF/container.xml")
            root = ET.fromstring(container)

            rootfile = root.find(
                f".//{{{_CONTAINER_NS}}}rootfile"
                f"[@media-type='application/oebps-package+xml']"
            )
            if rootfile is None:
                logger.debug("No rootfile found in container.xml for %s", path)
                return _empty_metadata()

            opf_path = rootfile.get("full-path", "")
            if not opf_path:
                return _empty_metadata()

            # Parse OPF for Dublin Core metadata
            opf_data = zf.read(opf_path)
            opf_root = ET.fromstring(opf_data)

            author_el = opf_root.find(f".//{{{_DC_NS}}}creator")
            title_el = opf_root.find(f".//{{{_DC_NS}}}title")

            return {
                "author": (author_el.text or "").strip() if author_el is not None else "",
                "title": (title_el.text or "").strip() if title_el is not None else "",
            }
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        logger.debug("Could not extract epub metadata from %s: %s", path, exc)
        return _empty_metadata()


def extract_mobi_metadata(path: Path) -> dict[str, str]:
    """Extract author and title from a mobi file using ebook-meta (Calibre).

    Args:
        path: Path to the mobi file.

    Returns:
        Dict with 'author' and 'title' keys (empty strings if not found).
    """
    import subprocess

    if not path.exists():
        return _empty_metadata()

    try:
        result = subprocess.run(
            ["ebook-meta", str(path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            logger.debug("ebook-meta failed for %s: %s", path, result.stderr)
            return _empty_metadata()

        metadata = _empty_metadata()
        for line in result.stdout.splitlines():
            if line.startswith("Title"):
                # Format: "Title               : The Great Book"
                _, _, value = line.partition(":")
                metadata["title"] = value.strip()
            elif line.startswith("Author(s)"):
                _, _, value = line.partition(":")
                # ebook-meta may list "Author [sort key]" — take name before bracket
                author = value.strip()
                if "[" in author:
                    author = author[: author.index("[")].strip()
                metadata["author"] = author

        return metadata
    except FileNotFoundError:
        logger.debug("ebook-meta not found; cannot extract mobi metadata")
        return _empty_metadata()
    except subprocess.TimeoutExpired:
        logger.debug("ebook-meta timed out for %s", path)
        return _empty_metadata()


def extract_metadata(path: Path) -> dict[str, str]:
    """Extract author and title metadata from an ebook file.

    Dispatches to format-specific extractors based on file extension.

    Args:
        path: Path to the ebook file.

    Returns:
        Dict with 'author' and 'title' keys (empty strings if not found
        or format not supported).
    """
    suffix = path.suffix.lower()

    if suffix == ".epub":
        return extract_epub_metadata(path)
    if suffix == ".mobi":
        return extract_mobi_metadata(path)

    return _empty_metadata()
