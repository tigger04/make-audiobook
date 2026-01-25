# ABOUTME: Tests for configuration and path utilities.
# ABOUTME: Verifies config persistence and path constant definitions.

"""Tests for config and paths utilities."""

import json
import pytest
from pathlib import Path

from gui.utils.paths import VOICES_DIR, CACHE_DIR, CONFIG_FILE, get_script_path
from gui.utils.config import load_config, save_config, get_default_config


class TestPaths:
    """Tests for path constants and utilities."""

    def test_voices_dir_is_path(self):
        """Test VOICES_DIR is a Path object."""
        assert isinstance(VOICES_DIR, Path)

    def test_voices_dir_is_in_local_share(self):
        """Test VOICES_DIR points to ~/.local/share/piper/voices."""
        assert str(VOICES_DIR).endswith("piper/voices")
        assert ".local/share" in str(VOICES_DIR)

    def test_cache_dir_is_path(self):
        """Test CACHE_DIR is a Path object."""
        assert isinstance(CACHE_DIR, Path)

    def test_cache_dir_is_in_cache(self):
        """Test CACHE_DIR points to ~/.cache/make-audiobook."""
        assert str(CACHE_DIR).endswith("make-audiobook")
        assert ".cache" in str(CACHE_DIR)

    def test_config_file_is_path(self):
        """Test CONFIG_FILE is a Path object."""
        assert isinstance(CONFIG_FILE, Path)

    def test_config_file_is_json(self):
        """Test CONFIG_FILE has .json extension."""
        assert CONFIG_FILE.suffix == ".json"

    def test_get_script_path_returns_path(self):
        """Test get_script_path returns a Path object."""
        result = get_script_path()
        assert isinstance(result, Path)


class TestConfig:
    """Tests for config load/save utilities."""

    @pytest.fixture
    def config_file(self, tmp_path):
        """Provide a temporary config file path."""
        return tmp_path / "settings.json"

    def test_get_default_config_returns_dict(self):
        """Test default config is a dictionary."""
        config = get_default_config()
        assert isinstance(config, dict)

    def test_default_config_has_required_keys(self):
        """Test default config has all expected keys."""
        config = get_default_config()
        assert "last_voice" in config
        assert "length_scale" in config
        assert "window_geometry" in config

    def test_default_length_scale_is_1_5(self):
        """Test default length_scale is 1.5."""
        config = get_default_config()
        assert config["length_scale"] == 1.5

    def test_save_config_creates_file(self, config_file):
        """Test save_config creates the config file."""
        config = {"test_key": "test_value"}
        save_config(config, config_file)
        assert config_file.exists()

    def test_save_config_writes_valid_json(self, config_file):
        """Test save_config writes valid JSON."""
        config = {"key1": "value1", "key2": 42}
        save_config(config, config_file)
        content = config_file.read_text()
        parsed = json.loads(content)
        assert parsed == config

    def test_save_config_creates_parent_dirs(self, tmp_path):
        """Test save_config creates parent directories."""
        nested_path = tmp_path / "deep" / "nested" / "config.json"
        save_config({"test": True}, nested_path)
        assert nested_path.exists()

    def test_load_config_reads_file(self, config_file):
        """Test load_config reads saved values from file."""
        saved = {"last_voice": "en_US-ryan-high", "length_scale": 1.2}
        config_file.write_text(json.dumps(saved))
        result = load_config(config_file)
        # Saved values should be present
        assert result["last_voice"] == "en_US-ryan-high"
        assert result["length_scale"] == 1.2

    def test_load_config_returns_default_for_missing_file(self, config_file):
        """Test load_config returns default when file missing."""
        result = load_config(config_file)
        assert result == get_default_config()

    def test_load_config_returns_default_for_invalid_json(self, config_file):
        """Test load_config returns default for corrupted file."""
        config_file.write_text("not valid json {{{")
        result = load_config(config_file)
        assert result == get_default_config()

    def test_load_save_roundtrip(self, config_file):
        """Test config survives save/load cycle with saved values preserved."""
        original = {
            "last_voice": "en_GB-alba-medium",
            "length_scale": 1.8,
            "window_geometry": {"x": 100, "y": 200, "width": 800, "height": 600},
        }
        save_config(original, config_file)
        loaded = load_config(config_file)
        # Saved values should be preserved
        assert loaded["last_voice"] == original["last_voice"]
        assert loaded["length_scale"] == original["length_scale"]
        assert loaded["window_geometry"] == original["window_geometry"]

    def test_config_merges_with_defaults(self, config_file):
        """Test partial config merges with defaults."""
        # Save only partial config
        partial = {"last_voice": "test-voice"}
        config_file.write_text(json.dumps(partial))

        result = load_config(config_file)
        # Should have saved value
        assert result["last_voice"] == "test-voice"
        # Should have default for missing keys
        assert result["length_scale"] == 1.5
