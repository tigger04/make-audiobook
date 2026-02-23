# ABOUTME: Path constants for make-audiobook GUI.
# ABOUTME: Defines standard locations for voices, cache, and configuration.

"""Path constants and utilities for make-audiobook GUI."""

import os
from pathlib import Path
from typing import Optional

# Standard directories
HOME = Path.home()

# Piper voice models directory
VOICES_DIR = HOME / ".local" / "share" / "piper" / "voices"

# Application cache directory
CACHE_DIR = HOME / ".cache" / "make-audiobook"

# Configuration file
CONFIG_FILE = HOME / ".config" / "make-audiobook" / "settings.json"

# Common binary paths to search when running as macOS app bundle.
# These paths may not be in PATH when launched from Finder.
COMMON_BIN_PATHS = [
    "/opt/homebrew/bin",      # Homebrew on Apple Silicon
    "/opt/homebrew/sbin",
    "/usr/local/bin",         # Homebrew on Intel, manual installs
    "/usr/local/sbin",
    "~/.local/bin",           # pipx, user installs (piper-tts)
    "/usr/bin",
    "/bin",
    "/usr/sbin",
    "/sbin",
]


def get_expanded_path() -> str:
    """Return PATH with common binary locations prepended.

    When launched as a macOS .app bundle, the process may not have
    the user's shell PATH. This function prepends common locations
    (Homebrew, pipx, etc.) so they take priority over system defaults.
    This ensures e.g. /opt/homebrew/bin/bash (5+) is found before
    /bin/bash (3.2) when resolving `#!/usr/bin/env bash`.

    Returns:
        Colon-separated PATH string with common locations prepended.
    """
    current_path = os.environ.get("PATH", "")
    current_parts = current_path.split(os.pathsep) if current_path else []

    # Prepend common paths so Homebrew/user tools take priority
    prepend_entries: list[str] = []
    seen: set[str] = set()
    for path in COMMON_BIN_PATHS:
        expanded = os.path.expanduser(path)
        if expanded not in seen:
            prepend_entries.append(expanded)
            seen.add(expanded)

    # Append existing PATH entries, skipping duplicates
    for entry in current_parts:
        if entry and entry not in seen:
            prepend_entries.append(entry)
            seen.add(entry)

    return os.pathsep.join(prepend_entries)


def find_executable(name: str) -> Optional[Path]:
    """Find an executable by name, searching expanded PATH.

    Args:
        name: The executable name to find (e.g., "ffmpeg", "piper")

    Returns:
        Path to the executable if found, None otherwise.
    """
    expanded_path = get_expanded_path()

    for directory in expanded_path.split(os.pathsep):
        if not directory:
            continue
        candidate = Path(directory) / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate

    return None


def get_script_path() -> Path:
    """Return the path to the make-audiobook script.

    Searches in the package directory first, then in expanded PATH.
    """
    # First, look relative to this module
    module_dir = Path(__file__).parent.parent.parent
    script_path = module_dir / "make-audiobook"
    if script_path.exists():
        return script_path

    # Search in expanded PATH
    found = find_executable("make-audiobook")
    if found:
        return found

    # Fallback: assume it's in PATH
    return Path("make-audiobook")
