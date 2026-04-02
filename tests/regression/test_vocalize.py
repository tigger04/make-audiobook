# ABOUTME: Tests for the vocalize CLI script.
# ABOUTME: Covers script structure, flag parsing, and dry-run behaviour (no TTS invoked).

import re
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent.parent / "vocalize"
KOKORO_VOICE_PATTERN = re.compile(r"^[abf]{2}_\w+$|^[abf]m_\w+$")


# ---------------------------------------------------------------------------
# Script structure (RT-34.2 and supporting checks)
# ---------------------------------------------------------------------------


class TestVocalizeStructure:
    """Verify vocalize has required script structure."""

    def test_vocalize_script_exists_RT34_2(self):
        assert SCRIPT_PATH.exists(), "vocalize script not found"

    def test_vocalize_script_is_executable_RT34_2(self):
        assert SCRIPT_PATH.stat().st_mode & 0o111, "vocalize is not executable"

    def test_vocalize_has_bash_shebang(self):
        lines = SCRIPT_PATH.read_text().splitlines()
        assert lines[0] == "#!/usr/bin/env bash"

    def test_vocalize_has_aboutme_comments(self):
        lines = SCRIPT_PATH.read_text().splitlines()
        aboutme = [l for l in lines[:5] if l.startswith("# ABOUTME:")]
        assert len(aboutme) >= 2

    def test_vocalize_has_set_euo_pipefail(self):
        header = "\n".join(SCRIPT_PATH.read_text().splitlines()[:10])
        assert "set -euo pipefail" in header

    def test_vocalize_has_ifs_safety_header(self):
        header = "\n".join(SCRIPT_PATH.read_text().splitlines()[:10])
        assert "IFS=$'\\n\\t'" in header


# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------


class TestVocalizeFlags:
    """Test CLI flag handling."""

    def test_vocalize_help_exits_zero(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--help"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0

    def test_vocalize_help_shows_usage(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--help"],
            capture_output=True, text=True, timeout=5,
        )
        assert "usage" in result.stdout.lower() or "usage" in result.stderr.lower()

    def test_vocalize_short_help_exits_zero(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "-h"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0

    def test_vocalize_version_exits_zero(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--version"],
            capture_output=True, text=True, timeout=5,
        )
        assert result.returncode == 0

    def test_vocalize_version_shows_version_string(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--version"],
            capture_output=True, text=True, timeout=5,
        )
        assert "vocalize" in result.stdout.lower() or "vocalize" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Dry-run: txt input (AC34.1, RT-34.1)
# ---------------------------------------------------------------------------


class TestVocalizeDryRunTxt:
    """Verify dry-run behaviour for txt input."""

    def test_vocalize_dry_run_txt_logs_mp3_target_RT34_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "sample.txt"
            txt.write_text("Hello world.")
            result = subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", str(txt)],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            combined = result.stdout + result.stderr
            assert "sample.mp3" in combined

    def test_vocalize_dry_run_txt_creates_no_file_RT34_7(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "sample.txt"
            txt.write_text("Hello world.")
            subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", str(txt)],
                capture_output=True, text=True, timeout=10,
            )
            assert not (Path(tmpdir) / "sample.mp3").exists()


# ---------------------------------------------------------------------------
# Dry-run: md input (AC34.2, RT-34.3)
# ---------------------------------------------------------------------------


class TestVocalizeDryRunMd:
    """Verify dry-run behaviour for md input."""

    def test_vocalize_dry_run_md_logs_mp3_target_RT34_3(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "notes.md"
            md.write_text("# Title\n\nSome text.")
            result = subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", str(md)],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            combined = result.stdout + result.stderr
            assert "notes.mp3" in combined


# ---------------------------------------------------------------------------
# Voice selection (AC34.3, AC34.4)
# ---------------------------------------------------------------------------


class TestVocalizeVoiceSelection:
    """Verify voice selection behaviour."""

    def test_vocalize_dry_run_no_voice_logs_kokoro_voice_RT34_4(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "t.txt"
            txt.write_text("text")
            result = subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", str(txt)],
                capture_output=True, text=True, timeout=10,
            )
            combined = result.stdout + result.stderr
            # Should log a voice key matching Kokoro voice naming convention
            assert any(
                re.search(r"\b[abf]{1,2}[mf]_\w+\b", line)
                for line in combined.splitlines()
            ), f"No Kokoro voice key found in output:\n{combined}"

    def test_vocalize_dry_run_explicit_voice_used_RT34_5(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "t.txt"
            txt.write_text("text")
            result = subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", "--voice=bm_lewis", str(txt)],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            combined = result.stdout + result.stderr
            assert "bm_lewis" in combined


# ---------------------------------------------------------------------------
# --output flag (AC34.5, RT-34.6)
# ---------------------------------------------------------------------------


class TestVocalizeOutputFlag:
    """Verify --output flag behaviour."""

    def test_vocalize_dry_run_output_flag_logs_custom_path_RT34_6(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            txt = Path(tmpdir) / "t.txt"
            txt.write_text("text")
            out = Path(tmpdir) / "custom.mp3"
            result = subprocess.run(
                [str(SCRIPT_PATH), "--dry-run", f"--output={out}", str(txt)],
                capture_output=True, text=True, timeout=10,
            )
            assert result.returncode == 0
            combined = result.stdout + result.stderr
            assert "custom.mp3" in combined
