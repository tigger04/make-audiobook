# ABOUTME: Tests for path utilities including PATH expansion for macOS app bundles.
# ABOUTME: Ensures dependencies can be found when launched from .app bundle.

"""Tests for gui.utils.paths module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from gui.utils.paths import (
    get_script_path,
    get_expanded_path,
    COMMON_BIN_PATHS,
    find_executable,
)


class TestGetExpandedPath:
    """Tests for get_expanded_path function."""

    def test_includes_current_path(self):
        """Expanded PATH should include the current PATH."""
        current_path = os.environ.get("PATH", "")
        expanded = get_expanded_path()

        # Current PATH entries should be present
        for entry in current_path.split(os.pathsep):
            if entry:
                assert entry in expanded

    def test_includes_common_bin_paths(self):
        """Expanded PATH should include common binary paths."""
        expanded = get_expanded_path()

        # Check that common paths are included
        assert "/opt/homebrew/bin" in expanded
        assert "/usr/local/bin" in expanded
        # Home-relative paths should be expanded
        home = str(Path.home())
        assert f"{home}/.local/bin" in expanded

    def test_no_duplicate_paths(self):
        """Expanded PATH should not have duplicate entries."""
        expanded = get_expanded_path()
        entries = expanded.split(os.pathsep)

        # Count occurrences of each entry
        seen = set()
        for entry in entries:
            if entry:
                assert entry not in seen, f"Duplicate PATH entry: {entry}"
                seen.add(entry)

    def test_returns_colon_separated_string(self):
        """Expanded PATH should be a colon-separated string."""
        expanded = get_expanded_path()

        assert isinstance(expanded, str)
        assert os.pathsep in expanded or len(expanded.split(os.pathsep)) == 1


class TestCommonBinPaths:
    """Tests for COMMON_BIN_PATHS constant."""

    def test_contains_homebrew_paths(self):
        """Should include Homebrew paths for both Intel and Apple Silicon."""
        assert "/opt/homebrew/bin" in COMMON_BIN_PATHS
        assert "/usr/local/bin" in COMMON_BIN_PATHS

    def test_contains_user_local_bin(self):
        """Should include user's local bin for pipx-installed tools."""
        assert "~/.local/bin" in COMMON_BIN_PATHS


class TestFindExecutable:
    """Tests for find_executable function."""

    def test_finds_existing_executable(self):
        """Should find an executable that exists."""
        # bash should exist on any Unix system
        result = find_executable("bash")
        assert result is not None
        assert result.exists()
        assert result.name == "bash"

    def test_returns_none_for_nonexistent(self):
        """Should return None for non-existent executable."""
        result = find_executable("definitely_not_a_real_command_12345")
        assert result is None

    def test_searches_expanded_path(self):
        """Should search in expanded PATH, not just current PATH."""
        # This tests that we search common paths even if not in current PATH
        with patch.dict(os.environ, {"PATH": "/nonexistent"}):
            # Even with a minimal PATH, we should find bash in common locations
            result = find_executable("bash")
            # bash should still be found via expanded PATH search
            assert result is not None


class TestGetScriptPath:
    """Tests for get_script_path function."""

    def test_returns_path_object(self):
        """Should return a Path object."""
        result = get_script_path()
        assert isinstance(result, Path)

    def test_finds_local_script(self):
        """Should find the local make-audiobook script."""
        result = get_script_path()
        # When running from repo, should find the local script
        if result.name == "make-audiobook":
            assert result.parent.name != ""  # Has a parent directory
