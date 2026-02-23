# ABOUTME: Tests for CatalogWorker that fetches voice catalog from HuggingFace.
# ABOUTME: Verifies HTTP fetching, caching, and signal emission.

"""Tests for CatalogWorker."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


from gui.workers.catalog_worker import CatalogWorker
from gui.models.voice import VoiceCatalog


# qapp fixture is provided by conftest.py


@pytest.fixture
def sample_voices_json():
    """Sample voices.json content."""
    return {
        "en_US": {
            "ryan": {
                "high": {
                    "key": "en_US-ryan-high",
                    "name": "Ryan",
                    "language": {"code": "en_US", "family": "en", "region": "US"},
                    "quality": "high",
                    "num_speakers": 1,
                    "speaker_id_map": {},
                    "files": {
                        "en_US-ryan-high.onnx": {"size_bytes": 63201294, "md5_digest": "abc123"},
                        "en_US-ryan-high.onnx.json": {"size_bytes": 5039, "md5_digest": "def456"},
                    },
                },
            },
        },
    }


@pytest.fixture
def cache_dir(tmp_path):
    """Provide a temporary cache directory."""
    cache = tmp_path / "cache"
    cache.mkdir()
    return cache


class TestCatalogWorker:
    """Tests for CatalogWorker."""

    def test_worker_creation(self, qapp, cache_dir):
        """Test CatalogWorker can be created."""
        worker = CatalogWorker(cache_dir=cache_dir)
        assert worker is not None

    def test_worker_has_catalog_ready_signal(self, qapp, cache_dir):
        """Test CatalogWorker has catalogReady signal."""
        worker = CatalogWorker(cache_dir=cache_dir)
        assert hasattr(worker, "catalogReady")

    def test_worker_has_error_signal(self, qapp, cache_dir):
        """Test CatalogWorker has error signal."""
        worker = CatalogWorker(cache_dir=cache_dir)
        assert hasattr(worker, "error")

    def test_worker_fetches_from_url(self, qapp, cache_dir, sample_voices_json):
        """Test CatalogWorker fetches from HuggingFace URL."""
        worker = CatalogWorker(cache_dir=cache_dir)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_voices_json

        received_catalog = []

        def on_catalog_ready(catalog):
            received_catalog.append(catalog)

        worker.catalogReady.connect(on_catalog_ready)

        with patch("gui.workers.catalog_worker.requests.get", return_value=mock_response):
            worker.run()

        assert len(received_catalog) == 1
        assert isinstance(received_catalog[0], VoiceCatalog)
        assert len(received_catalog[0].voices) == 1

    def test_worker_caches_result(self, qapp, cache_dir, sample_voices_json):
        """Test CatalogWorker caches the fetched catalog."""
        worker = CatalogWorker(cache_dir=cache_dir)
        cache_file = cache_dir / "voices_catalog.json"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_voices_json

        with patch("gui.workers.catalog_worker.requests.get", return_value=mock_response):
            worker.run()

        assert cache_file.exists()
        cached_data = json.loads(cache_file.read_text())
        assert "en_US" in cached_data

    def test_worker_uses_cache_if_fresh(self, qapp, cache_dir, sample_voices_json):
        """Test CatalogWorker uses cache if less than 24 hours old."""
        cache_file = cache_dir / "voices_catalog.json"
        cache_file.write_text(json.dumps(sample_voices_json))

        worker = CatalogWorker(cache_dir=cache_dir)

        received_catalog = []
        worker.catalogReady.connect(lambda c: received_catalog.append(c))

        with patch("gui.workers.catalog_worker.requests.get") as mock_get:
            worker.run()
            # Should not fetch from network
            mock_get.assert_not_called()

        assert len(received_catalog) == 1

    def test_worker_fetches_if_cache_stale(self, qapp, cache_dir, sample_voices_json):
        """Test CatalogWorker fetches if cache is older than 24 hours."""
        cache_file = cache_dir / "voices_catalog.json"
        cache_file.write_text(json.dumps(sample_voices_json))

        # Set modification time to 25 hours ago
        import os
        old_time = datetime.now() - timedelta(hours=25)
        os.utime(cache_file, (old_time.timestamp(), old_time.timestamp()))

        worker = CatalogWorker(cache_dir=cache_dir)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_voices_json

        with patch("gui.workers.catalog_worker.requests.get", return_value=mock_response) as mock_get:
            worker.run()
            # Should fetch from network
            mock_get.assert_called_once()

    def test_worker_emits_error_on_network_failure(self, qapp, cache_dir):
        """Test CatalogWorker emits error signal on network failure."""
        worker = CatalogWorker(cache_dir=cache_dir)

        received_errors = []
        worker.error.connect(lambda e: received_errors.append(e))

        with patch("gui.workers.catalog_worker.requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            worker.run()

        assert len(received_errors) == 1
        assert "Network error" in received_errors[0]

    def test_worker_force_refresh_bypasses_cache(self, qapp, cache_dir, sample_voices_json):
        """Test CatalogWorker force_refresh ignores cache."""
        cache_file = cache_dir / "voices_catalog.json"
        cache_file.write_text(json.dumps(sample_voices_json))

        worker = CatalogWorker(cache_dir=cache_dir, force_refresh=True)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_voices_json

        with patch("gui.workers.catalog_worker.requests.get", return_value=mock_response) as mock_get:
            worker.run()
            mock_get.assert_called_once()

    def test_worker_creates_cache_dir_if_missing(self, qapp, tmp_path, sample_voices_json):
        """Test CatalogWorker creates cache directory if it doesn't exist."""
        cache_dir = tmp_path / "nonexistent" / "cache"
        assert not cache_dir.exists()

        worker = CatalogWorker(cache_dir=cache_dir)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_voices_json

        with patch("gui.workers.catalog_worker.requests.get", return_value=mock_response):
            worker.run()

        assert cache_dir.exists()
