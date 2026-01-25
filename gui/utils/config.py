# ABOUTME: Configuration management for make-audiobook GUI.
# ABOUTME: Handles loading, saving, and defaulting of user preferences.

"""Configuration management for make-audiobook GUI."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from gui.utils.paths import CONFIG_FILE

logger = logging.getLogger(__name__)


def get_default_config() -> dict[str, Any]:
    """Return the default configuration dictionary."""
    return {
        "last_voice": None,
        "length_scale": 1.5,
        "random_voice": False,
        "random_filter": None,
        "window_geometry": None,
        "last_directory": None,
    }


def save_config(config: dict[str, Any], config_path: Path = CONFIG_FILE) -> None:
    """Save configuration to a JSON file.

    Creates parent directories if they don't exist.

    Args:
        config: Configuration dictionary to save
        config_path: Path to the config file (default: CONFIG_FILE)
    """
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def load_config(config_path: Path = CONFIG_FILE) -> dict[str, Any]:
    """Load configuration from a JSON file.

    Returns defaults if file doesn't exist or is corrupted.
    Merges loaded config with defaults for any missing keys.

    Args:
        config_path: Path to the config file (default: CONFIG_FILE)

    Returns:
        Configuration dictionary
    """
    defaults = get_default_config()

    if not config_path.exists():
        return defaults

    try:
        with open(config_path) as f:
            loaded = json.load(f)

        # Merge with defaults (loaded values override defaults)
        result = defaults.copy()
        result.update(loaded)
        return result

    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Failed to load config from %s: %s", config_path, e)
        return defaults
