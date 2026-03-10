# ABOUTME: Tests for the install-dependencies shell script.
# ABOUTME: Covers static analysis, CLI flags, and symlink creation behaviour.

import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "install-dependencies"


@pytest.fixture
def script_content():
    """Read the install-dependencies script content."""
    return SCRIPT_PATH.read_text()


@pytest.fixture
def script_lines(script_content):
    """Split script content into lines."""
    return script_content.splitlines()


def _non_comment_lines(lines):
    """Return lines that are not comments or blank."""
    for line in lines:
        stripped = line.lstrip()
        if stripped and not stripped.startswith("#"):
            yield line


# ---------------------------------------------------------------------------
# Static analysis: script structure
# ---------------------------------------------------------------------------


class TestInstallDepsStructure:
    """Verify script has required structure per coding standards."""

    def test_install_deps_has_bash_shebang(self, script_lines):
        assert script_lines[0] == "#!/usr/bin/env bash"

    def test_install_deps_has_aboutme_comments(self, script_lines):
        # ABOUTME comments must appear in the first 5 lines
        aboutme = [l for l in script_lines[:5] if l.startswith("# ABOUTME:")]
        assert len(aboutme) >= 2

    def test_install_deps_has_safety_header_set_euo_pipefail(self, script_lines):
        header = "\n".join(script_lines[:10])
        assert "set -euo pipefail" in header

    def test_install_deps_has_safety_header_ifs(self, script_lines):
        header = "\n".join(script_lines[:10])
        assert "IFS=$'\\n\\t'" in header

    def test_install_deps_defines_warn_function(self, script_content):
        assert "warn()" in script_content

    def test_install_deps_defines_die_function(self, script_content):
        assert "die()" in script_content

    def test_install_deps_defines_info_function(self, script_content):
        assert "info()" in script_content

    def test_install_deps_defines_checkmark_function(self, script_content):
        assert "checkmark()" in script_content


# ---------------------------------------------------------------------------
# Static analysis: prohibited patterns
# ---------------------------------------------------------------------------


class TestInstallDepsProhibitedPatterns:
    """Verify script does not contain forbidden patterns."""

    def test_install_deps_never_writes_to_shell_config(self, script_lines):
        """Script must never modify .bashrc, .bash_profile, or .zshrc."""
        forbidden = [".bashrc", ".bash_profile", ".zshrc"]
        for i, line in enumerate(script_lines):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            for cfg in forbidden:
                assert cfg not in line, (
                    f"Line {i + 1}: script references shell config '{cfg}': {line}"
                )

    def test_install_deps_never_uses_bare_pip_install(self, script_lines):
        """Script must use pipx, never bare pip install."""
        for i, line in enumerate(script_lines):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if "pip install" in stripped and "pipx install" not in stripped:
                assert False, (
                    f"Line {i + 1}: bare 'pip install' found: {line}"
                )

    def test_install_deps_uses_command_v_not_which(self, script_lines):
        """Script must use 'command -v', never 'which'."""
        for i, line in enumerate(script_lines):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            # Match 'which' used as a command, not in quoted user instructions
            if stripped.startswith("which "):
                assert False, (
                    f"Line {i + 1}: uses 'which' instead of 'command -v': {line}"
                )


# ---------------------------------------------------------------------------
# Static analysis: multi-distro support
# ---------------------------------------------------------------------------


class TestInstallDepsMultiDistro:
    """Verify script handles multiple Linux package managers."""

    def test_install_deps_supports_apt(self, script_content):
        assert "apt-get" in script_content or "apt " in script_content

    def test_install_deps_supports_dnf(self, script_content):
        assert "dnf" in script_content

    def test_install_deps_supports_pacman(self, script_content):
        assert "pacman" in script_content

    def test_install_deps_supports_apk(self, script_content):
        assert "apk" in script_content

    def test_install_deps_supports_nix(self, script_content):
        assert "nix" in script_content.lower()

    def test_install_deps_handles_unknown_package_manager(self, script_content):
        """Script should print instructions when no known PM is found."""
        assert "unknown" in script_content.lower() or "unsupported" in script_content.lower()


# ---------------------------------------------------------------------------
# CLI flags
# ---------------------------------------------------------------------------


class TestInstallDepsFlags:
    """Test CLI flag handling."""

    def test_install_deps_help_flag_exits_zero(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0

    def test_install_deps_help_flag_shows_usage(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert "usage" in result.stdout.lower()

    def test_install_deps_short_help_flag(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "-h"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0
        assert "usage" in result.stdout.lower()

    def test_install_deps_version_flag_exits_zero(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0

    def test_install_deps_version_flag_shows_version(self):
        result = subprocess.run(
            [str(SCRIPT_PATH), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert "install-dependencies" in result.stdout


# ---------------------------------------------------------------------------
# Symlink creation
# ---------------------------------------------------------------------------


class TestInstallDepsSymlinks:
    """Test symlink creation behaviour."""

    def test_install_deps_link_only_creates_symlinks(self):
        """--link-only flag should create symlinks without installing packages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake project directory with executables
            src_dir = Path(tmpdir) / "project"
            src_dir.mkdir()
            for exe in ["make-audiobook", "piper-voices-setup", "install-dependencies"]:
                exe_path = src_dir / exe
                exe_path.write_text("#!/usr/bin/env bash\necho test\n")
                exe_path.chmod(0o755)

            # Copy the real script content into the fake project
            real_content = SCRIPT_PATH.read_text()
            (src_dir / "install-dependencies").write_text(real_content)
            (src_dir / "install-dependencies").chmod(0o755)

            fake_home = Path(tmpdir) / "home"
            fake_home.mkdir()

            env = os.environ.copy()
            env["HOME"] = str(fake_home)

            result = subprocess.run(
                [str(src_dir / "install-dependencies"), "--link-only"],
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )

            assert result.returncode == 0

            local_bin = fake_home / ".local" / "bin"
            assert (local_bin / "make-audiobook").is_symlink()
            assert (local_bin / "piper-voices-setup").is_symlink()

    def test_install_deps_link_only_does_not_create_self_symlink(self):
        """install-dependencies itself should not be symlinked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "project"
            src_dir.mkdir()
            for exe in ["make-audiobook", "piper-voices-setup", "install-dependencies"]:
                exe_path = src_dir / exe
                exe_path.write_text("#!/usr/bin/env bash\necho test\n")
                exe_path.chmod(0o755)

            real_content = SCRIPT_PATH.read_text()
            (src_dir / "install-dependencies").write_text(real_content)
            (src_dir / "install-dependencies").chmod(0o755)

            fake_home = Path(tmpdir) / "home"
            fake_home.mkdir()

            env = os.environ.copy()
            env["HOME"] = str(fake_home)

            subprocess.run(
                [str(src_dir / "install-dependencies"), "--link-only"],
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )

            local_bin = fake_home / ".local" / "bin"
            assert not (local_bin / "install-dependencies").exists()

    def test_install_deps_link_only_updates_existing_symlinks(self):
        """Re-running --link-only should update existing symlinks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "project"
            src_dir.mkdir()
            for exe in ["make-audiobook", "piper-voices-setup", "install-dependencies"]:
                exe_path = src_dir / exe
                exe_path.write_text("#!/usr/bin/env bash\necho test\n")
                exe_path.chmod(0o755)

            real_content = SCRIPT_PATH.read_text()
            (src_dir / "install-dependencies").write_text(real_content)
            (src_dir / "install-dependencies").chmod(0o755)

            fake_home = Path(tmpdir) / "home"
            fake_home.mkdir()

            env = os.environ.copy()
            env["HOME"] = str(fake_home)

            script = str(src_dir / "install-dependencies")

            # Run twice — second run should succeed without errors
            subprocess.run(
                [script, "--link-only"], capture_output=True, env=env, timeout=10,
            )
            result = subprocess.run(
                [script, "--link-only"],
                capture_output=True,
                text=True,
                env=env,
                timeout=10,
            )

            assert result.returncode == 0
            local_bin = fake_home / ".local" / "bin"
            assert (local_bin / "make-audiobook").is_symlink()

    def test_install_deps_link_only_skips_non_symlink_files(self):
        """If a regular file exists at the target, do not overwrite it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = Path(tmpdir) / "project"
            src_dir.mkdir()
            for exe in ["make-audiobook", "piper-voices-setup", "install-dependencies"]:
                exe_path = src_dir / exe
                exe_path.write_text("#!/usr/bin/env bash\necho test\n")
                exe_path.chmod(0o755)

            real_content = SCRIPT_PATH.read_text()
            (src_dir / "install-dependencies").write_text(real_content)
            (src_dir / "install-dependencies").chmod(0o755)

            fake_home = Path(tmpdir) / "home"
            fake_home.mkdir()
            local_bin = fake_home / ".local" / "bin"
            local_bin.mkdir(parents=True)

            # Pre-create a regular file (not a symlink)
            existing = local_bin / "make-audiobook"
            existing.write_text("existing file")

            env = os.environ.copy()
            env["HOME"] = str(fake_home)

            subprocess.run(
                [str(src_dir / "install-dependencies"), "--link-only"],
                capture_output=True,
                env=env,
                timeout=10,
            )

            # Should NOT have been overwritten
            assert not existing.is_symlink()
            assert existing.read_text() == "existing file"
