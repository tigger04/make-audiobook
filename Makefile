# ABOUTME: Makefile for make-audiobook project.
# ABOUTME: Provides standard targets for building, testing, and running the GUI.

.PHONY: help install install-gui test test-gui gui lint clean

PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest

help:
	@echo "make-audiobook - Convert documents to audiobooks using Piper TTS"
	@echo ""
	@echo "Usage:"
	@echo "  make install      Install CLI dependencies"
	@echo "  make install-gui  Install GUI dependencies (creates venv)"
	@echo "  make gui          Launch the GUI"
	@echo "  make test         Run all tests"
	@echo "  make test-gui     Run GUI tests only"
	@echo "  make lint         Run linters"
	@echo "  make clean        Remove build artifacts"

install:
	@echo "Running install-dependencies script..."
	./install-dependencies

install-gui: $(VENV)/bin/activate
	@echo "GUI dependencies installed."

$(VENV)/bin/activate: requirements-gui.txt
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-gui.txt
	@touch $(VENV)/bin/activate

gui: install-gui
	@echo "Launching make-audiobook GUI..."
	$(VENV_BIN)/python -m gui

test: test-gui
	@echo "All tests passed."

test-gui: install-gui
	@echo "Running GUI tests..."
	$(PYTEST) tests/gui/ -v

lint: install-gui
	@echo "Running linters..."
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check gui/ tests/; \
	else \
		echo "Ruff not installed, skipping Python linting"; \
	fi
	@if command -v shellcheck >/dev/null 2>&1; then \
		shellcheck make-audiobook piper-voices-setup install-dependencies; \
	else \
		echo "ShellCheck not installed, skipping shell linting"; \
	fi

clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(VENV)
	rm -rf __pycache__ gui/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
