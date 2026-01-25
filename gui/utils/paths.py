# ABOUTME: Path constants for make-audiobook GUI.
# ABOUTME: Defines standard locations for voices, cache, and configuration.

"""Path constants and utilities for make-audiobook GUI."""

from pathlib import Path

# Standard directories
HOME = Path.home()

# Piper voice models directory
VOICES_DIR = HOME / ".local" / "share" / "piper" / "voices"

# Application cache directory
CACHE_DIR = HOME / ".cache" / "make-audiobook"

# Configuration file
CONFIG_FILE = HOME / ".config" / "make-audiobook" / "settings.json"


def get_script_path() -> Path:
    """Return the path to the make-audiobook script.

    Searches in the package directory first, then in PATH.
    """
    # First, look relative to this module
    module_dir = Path(__file__).parent.parent.parent
    script_path = module_dir / "make-audiobook"
    if script_path.exists():
        return script_path

    # Fallback: assume it's in PATH
    return Path("make-audiobook")
