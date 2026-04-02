# ABOUTME: Tests for the speak CLI script.
# ABOUTME: Covers script structure, player selection, stderr path output, and dry-run behaviour.

import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent.parent / "speak"


# ---------------------------------------------------------------------------
# Script structure
# ---------------------------------------------------------------------------


class TestSpeakStructure:
    """Verify speak has required script structure."""

    def test_speak_script_exists(self):
        assert SCRIPT_PATH.exists(), "speak script not found"

    def test_speak_script_is_executable(self):
        assert SCRIPT_PATH.stat().st_mode & 0o111, "speak is not executable"

    def test_speak_has_bash_shebang(self):
        lines = SCRIPT_PATH.read_text().splitlines()
        assert lines[0] == "#!/usr/bin/env bash"

    def test_speak_has_aboutme_comments(self):
        lines = SCRIPT_PATH.read_text().splitlines()
        aboutme = [l for l in lines[:5] if l.startswith("# ABOUTME:")]
        assert len(aboutme) >= 2

    def test_speak_has_set_euo_pipefail(self):
        header = "\n".join(SCRIPT_PATH.read_text().splitlines()[:10])
        assert "set -euo pipefail" in header

    def test_speak_has_ifs_safety_header(self):
        header = "\n".join(SCRIPT_PATH.read_text().splitlines()[:10])
        assert "IFS=$'\\n\\t'" in header


# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------


class TestSpeakFlags:
    """Test CLI flag handling."""

    def test_speak_help_exits_zero(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--help"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0

    def test_speak_help_shows_usage(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--help"],
            capture_output=True, text=True, timeout=5,
        )
        assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()

    def test_speak_version_exits_zero(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--version"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Dry-run: stderr path output (AC35.2, RT-35.1)
# ---------------------------------------------------------------------------


class TestSpeakDryRun:
    """Verify dry-run behaviour."""

    def test_speak_dry_run_logs_mp3_path_to_stderr_RT35_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "sample.txt"
            txt.write_text("Hello.")
            result = subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", str(txt)],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            assert ".mp3" in result.stderr

    def test_speak_dry_run_creates_no_file_RT35_3(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "sample.txt"
            txt.write_text("Hello.")
            result = subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", str(txt)],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            # Extract path from stderr and verify no file was created
            for token in result.stderr.split():
                if token.endswith(".mp3"):
                    assert not Path(token).exists(), f"Dry-run created file: {token}"
                    break

    def test_speak_dry_run_logs_player_RT35_10(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "sample.txt"
            txt.write_text("Hello.")
            result = subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", str(txt)],
                capture_output=True, text=True, timeout=10,
            )
            combined = result.stdout + result.stderr
            # Should mention some player
            assert any(
                p in combined for p in ["afplay", "mpv", "vlc", "aplay"]
            )

    def test_speak_dry_run_voice_passthrough_RT35_4(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "sample.txt"
            txt.write_text("Hello.")
            result = subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", "--voice=af_bella", str(txt)],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            combined = result.stdout + result.stderr
            assert "af_bella" in combined


# ---------------------------------------------------------------------------
# Stdin (AC35.3, RT-35.2)
# ---------------------------------------------------------------------------


class TestSpeakStdin:
    """Verify speak reads from stdin."""

    def test_speak_dry_run_accepts_stdin_RT35_2(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--dry-run"],
            input="Hello from stdin.",
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert ".mp3" in result.stderr


# ---------------------------------------------------------------------------
# Player selection (AC35.6, RT-35.5 through RT-35.8)
# ---------------------------------------------------------------------------


class TestSpeakPlayerSelection:
    """Verify platform player selection logic."""

    def _run_with_speak_player(self, player_name: str) -> subprocess.CompletedProcess:
        """Run speak --dry-run with SPEAK_PLAYER set to a stub player."""
        with tempfile.TemporaryDirectory() as fake_bin:
            fake_player = Path(fake_bin) / player_name
            fake_player.write_text("#!/usr/bin/env bash\nexit 0\n")
            fake_player.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = f"{fake_bin}:{env.get('PATH', '')}"
            env["SPEAK_PLAYER"] = player_name

            with tempfile.TemporaryDirectory() as tmpdir:
                txt = Path(tmpdir) / "t.txt"
                txt.write_text("text")
                return subprocess.run(
                    [str(SCRIPT_PATH), "--dry-run", str(txt)],
                    capture_output=True, text=True, timeout=10, env=env,
                )

    def test_speak_selects_mpv_via_speak_player_env_RT35_6(self):
        result = self._run_with_speak_player("mpv")
        combined = result.stdout + result.stderr
        assert "mpv" in combined

    def test_speak_selects_vlc_via_speak_player_env_RT35_7(self):
        result = self._run_with_speak_player("vlc")
        combined = result.stdout + result.stderr
        assert "vlc" in combined

    def test_speak_selects_aplay_via_speak_player_env_RT35_8(self):
        result = self._run_with_speak_player("aplay")
        combined = result.stdout + result.stderr
        assert "aplay" in combined


# ---------------------------------------------------------------------------
# No player available (AC35.7, RT-35.9)
# ---------------------------------------------------------------------------


class TestSpeakNoPlayer:
    """Verify speak fails informatively when no player is found.

    Uses SPEAK_PLAYER=<nonexistent> to force the failure path reliably on all
    platforms (avoids afplay always being present on macOS).
    """

    def _env_with_no_player(self) -> dict:
        env = os.environ.copy()
        env["SPEAK_PLAYER"] = "no_such_player_xyz"
        return env

    def test_speak_exits_nonzero_when_no_player_RT35_9(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "t.txt"
            txt.write_text("text")
            result = subprocess.run(
                [str(SCRIPT_PATH), str(txt)],
                capture_output=True, text=True, timeout=10,
                env=self._env_with_no_player(),
            )
            assert result.returncode != 0

    def test_speak_names_tried_player_in_error_RT35_9(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "t.txt"
            txt.write_text("text")
            result = subprocess.run(
                [str(SCRIPT_PATH), str(txt)],
                capture_output=True, text=True, timeout=10,
                env=self._env_with_no_player(),
            )
            combined = result.stdout + result.stderr
            assert "no_such_player_xyz" in combined
