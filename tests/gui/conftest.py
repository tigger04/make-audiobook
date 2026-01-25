# ABOUTME: Shared pytest fixtures for GUI tests.
# ABOUTME: Provides a single QApplication instance for all tests.

"""Shared pytest fixtures for GUI tests."""

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Provide a single QApplication for all GUI tests.

    QApplication can only be created once per process, so this
    fixture is session-scoped and shared across all test modules.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app - it causes issues with test cleanup
