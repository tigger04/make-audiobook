# ABOUTME: Makefile for make-audiobook project.
# ABOUTME: Provides standard targets for building, testing, and running the GUI.

.PHONY: help install install-gui test test-gui gui lint clean build-macos release

PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest

VERSION ?= $(shell git describe --tags --abbrev=0 2>/dev/null || echo "0.1.0")

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
	@echo ""
	@echo "Release:"
	@echo "  make build-macos  Build macOS .app and .dmg"
	@echo "  make release      Tag and push a new release (VERSION=x.y.z)"

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
	rm -rf build dist
	rm -rf __pycache__ gui/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -rf *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

build-macos:
	@echo "Building macOS app bundle..."
	./scripts/build-macos.sh $(VERSION)

release:
	@if [ -z "$(VERSION)" ] || [ "$(VERSION)" = "0.1.0" ]; then \
		echo "Error: Please specify VERSION, e.g., make release VERSION=1.0.0"; \
		exit 1; \
	fi
	@echo "Creating release $(VERSION)..."
	@echo "Running tests first..."
	$(MAKE) test
	@echo "Tagging v$(VERSION)..."
	git tag -a "v$(VERSION)" -m "Release $(VERSION)"
	git push origin "v$(VERSION)"
	@echo ""
	@echo "Release v$(VERSION) tagged and pushed."
	@echo "GitHub Actions will build the macOS DMG and create the release."
