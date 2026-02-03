# ABOUTME: Makefile for make-audiobook project.
# ABOUTME: Provides standard targets for building, testing, and running the GUI.

.PHONY: help install install-gui install-voices test test-gui gui lint clean build-macos release

PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin
PIP := $(VENV_BIN)/pip
PYTEST := $(VENV_BIN)/pytest

CURRENT_VERSION := $(shell git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || echo "0.1.0")
ifdef VERSION
  RELEASE_VERSION := $(VERSION)
else
  RELEASE_VERSION = $(shell echo "$(CURRENT_VERSION)" | awk -F. '{printf "%d.%d.0", $$1, $$2+1}')
endif

help:
	@echo "make-audiobook - Convert documents to audiobooks using Piper TTS"
	@echo ""
	@echo "Usage:"
	@echo "  make install        Install CLI dependencies"
	@echo "  make install-gui    Install GUI dependencies and default voices"
	@echo "  make install-voices Install default Piper voices"
	@echo "  make gui          Launch the GUI"
	@echo "  make test         Run all tests"
	@echo "  make test-gui     Run GUI tests only"
	@echo "  make lint         Run linters"
	@echo "  make clean        Remove build artifacts"
	@echo ""
	@echo "Release:"
	@echo "  make build-macos          Build macOS .app and .dmg"
	@echo "  make release              Auto-increment minor version, build, tag, push"
	@echo "  make release VERSION=x.y.z  Release with explicit version"

install:
	@echo "Running install-dependencies script..."
	./install-dependencies

install-gui: $(VENV)/bin/activate install-voices
	@echo "GUI dependencies installed."

install-voices:
	@echo "Installing default voices..."
	./piper-voices-setup

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
	./scripts/build-macos.sh $(or $(VERSION),$(CURRENT_VERSION))

release:
	@echo "Creating release $(RELEASE_VERSION) (current: $(CURRENT_VERSION))..."
	@echo ""
	@echo "Running tests first..."
	$(MAKE) test
	@echo ""
	@echo "Building macOS DMG..."
	./scripts/build-macos.sh $(RELEASE_VERSION)
	@echo ""
	@echo "Tagging v$(RELEASE_VERSION)..."
	git tag -a "v$(RELEASE_VERSION)" -m "Release $(RELEASE_VERSION)"
	git push origin "v$(RELEASE_VERSION)"
	@echo ""
	@echo "=== Release Summary ==="
	@echo "Version: $(RELEASE_VERSION)"
	@echo "Tag:     v$(RELEASE_VERSION)"
	@DMG_PATH="dist/make-audiobook-$(RELEASE_VERSION).dmg"; \
	if [ -f "$$DMG_PATH" ]; then \
		SHA256=$$(shasum -a 256 "$$DMG_PATH" | awk '{print $$1}'); \
		echo "DMG:     $$DMG_PATH"; \
		echo "SHA256:  $$SHA256"; \
	else \
		echo "DMG:     not found (CI will build it)"; \
	fi
	@echo ""
	@echo "GitHub Actions will create the GitHub Release and update the Homebrew tap."
