# ABOUTME: Application entry point for make-audiobook GUI.
# ABOUTME: Creates QApplication and launches the main window.

"""Application setup for make-audiobook GUI."""

from __future__ import annotations

import logging
import sys
from typing import Optional

from PySide6.QtWidgets import QApplication, QMessageBox

from gui.views.main_window import MainWindow
from gui.utils.paths import find_executable

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def check_dependencies() -> list[str]:
    """Check for required system dependencies.

    Uses expanded PATH to find executables in common locations
    (Homebrew, pipx, etc.) even when launched from .app bundle.

    Returns:
        List of missing dependencies
    """
    missing = []
    required = ["piper", "ffmpeg", "pandoc"]

    for cmd in required:
        if find_executable(cmd) is None:
            missing.append(cmd)

    return missing


def show_dependency_error(app: QApplication, missing: list[str]) -> None:
    """Show error dialog for missing dependencies."""
    msg = "The following dependencies are missing:\n\n"
    msg += "\n".join(f"  - {dep}" for dep in missing)
    msg += "\n\nPlease install them and restart the application."
    msg += "\n\nRun ./install-dependencies for automatic installation."

    QMessageBox.critical(None, "Missing Dependencies", msg)


def run(argv: Optional[list[str]] = None) -> int:
    """Run the make-audiobook GUI application.

    Args:
        argv: Command line arguments (default: sys.argv)

    Returns:
        Exit code
    """
    if argv is None:
        argv = sys.argv

    setup_logging()

    # Create application
    app = QApplication(argv)
    app.setApplicationName("make-audiobook")
    app.setOrganizationName("make-audiobook")

    # Check dependencies
    missing = check_dependencies()
    if missing:
        show_dependency_error(app, missing)
        return 1

    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception as e:
        logger.exception("Application error")
        QMessageBox.critical(None, "Error", f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run())
