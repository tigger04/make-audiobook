# ABOUTME: Utility modules for the make-audiobook GUI.
# ABOUTME: Provides path constants and configuration management.

"""Utility modules for make-audiobook GUI."""

from gui.utils.paths import VOICES_DIR, CACHE_DIR, CONFIG_FILE
from gui.utils.config import load_config, save_config

__all__ = ["VOICES_DIR", "CACHE_DIR", "CONFIG_FILE", "load_config", "save_config"]
