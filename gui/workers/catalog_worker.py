# ABOUTME: Background worker for fetching the Piper voice catalog from HuggingFace.
# ABOUTME: Handles HTTP requests, caching, and emits signals for GUI updates.

"""CatalogWorker for fetching and caching the Piper voice catalog."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from PySide6.QtCore import QObject, Signal

from gui.models.voice import VoiceCatalog
from gui.utils.paths import CACHE_DIR

logger = logging.getLogger(__name__)

# HuggingFace URL for Piper voices catalog
VOICES_CATALOG_URL = "https://huggingface.co/rhasspy/piper-voices/raw/main/voices.json"

# Cache duration: 24 hours
CACHE_TTL_HOURS = 24


class CatalogWorker(QObject):
    """Worker for fetching the voice catalog from HuggingFace.

    Fetches voices.json and caches it locally. Uses cached version
    if less than 24 hours old unless force_refresh is True.

    Signals:
        catalogReady(VoiceCatalog): Emitted when catalog is available
        error(str): Emitted on fetch failure
    """

    catalogReady = Signal(VoiceCatalog)
    error = Signal(str)

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        force_refresh: bool = False,
        parent: Optional[QObject] = None,
    ):
        """Initialise the CatalogWorker.

        Args:
            cache_dir: Directory for caching catalog (default: CACHE_DIR)
            force_refresh: Bypass cache and fetch from network
            parent: Parent QObject
        """
        super().__init__(parent)
        self._cache_dir = cache_dir or CACHE_DIR
        self._force_refresh = force_refresh
        self._cache_file = self._cache_dir / "voices_catalog.json"

    def run(self) -> None:
        """Fetch the voice catalog.

        Checks cache first (if not force_refresh), then fetches from network.
        Emits catalogReady on success, error on failure.
        """
        try:
            # Check cache first
            if not self._force_refresh and self._is_cache_valid():
                catalog = self._load_from_cache()
                if catalog is not None:
                    self.catalogReady.emit(catalog)
                    return

            # Fetch from network
            catalog = self._fetch_from_network()
            self.catalogReady.emit(catalog)

        except Exception as e:
            logger.exception("Failed to fetch voice catalog")
            self.error.emit(str(e))

    def _is_cache_valid(self) -> bool:
        """Check if cache file exists and is less than CACHE_TTL_HOURS old."""
        if not self._cache_file.exists():
            return False

        mtime = datetime.fromtimestamp(self._cache_file.stat().st_mtime)
        age = datetime.now() - mtime
        return age < timedelta(hours=CACHE_TTL_HOURS)

    def _load_from_cache(self) -> Optional[VoiceCatalog]:
        """Load catalog from cache file."""
        try:
            with open(self._cache_file) as f:
                data = json.load(f)
            return VoiceCatalog.from_dict(data)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to load cache: %s", e)
            return None

    def _fetch_from_network(self) -> VoiceCatalog:
        """Fetch catalog from HuggingFace and cache it."""
        logger.info("Fetching voice catalog from %s", VOICES_CATALOG_URL)

        response = requests.get(VOICES_CATALOG_URL, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Cache the result
        self._save_to_cache(data)

        return VoiceCatalog.from_dict(data)

    def _save_to_cache(self, data: dict) -> None:
        """Save catalog data to cache file."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        with open(self._cache_file, "w") as f:
            json.dump(data, f)
