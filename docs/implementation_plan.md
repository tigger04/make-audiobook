# GUI Implementation Plan

## Overview

Add a PySide6-based graphical user interface to make-audiobook, making the tool accessible to non-technical users with built-in voice management.

**Parent Issue**: [#1 - GUI interface](https://github.com/tigger04/make-audiobook/issues/1)

## Architecture

### Design Decisions

1. **Hybrid approach**: GUI calls existing `make-audiobook` bash script via `QProcess` for conversion (preserves tested logic), while voice management is reimplemented in Python for better progress callbacks.

2. **Voice catalog**: Fetch `voices.json` from HuggingFace with 24-hour cache:
   ```
   https://huggingface.co/rhasspy/piper-voices/raw/main/voices.json
   ```

3. **Threading model**:
   - `QProcess` for subprocess-based conversion
   - `QThread` workers for downloads and catalog fetching
   - Main thread never blocked

### Directory Structure

```
make-audiobook/
├── make-audiobook              # Existing (unchanged)
├── piper-voices-setup          # Existing (unchanged)
├── make-audiobook-gui          # Entry point script
├── gui/
│   ├── __init__.py
│   ├── __main__.py             # python -m gui
│   ├── app.py                  # QApplication setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── voice.py            # Voice dataclass, VoiceCatalog
│   │   └── conversion_job.py   # Job state
│   ├── views/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── file_list.py        # Drag-drop widget
│   │   ├── voice_browser.py    # HuggingFace catalog browser
│   │   ├── voice_manager.py    # Installed voices
│   │   ├── settings_panel.py   # Speed, metadata
│   │   └── progress_panel.py   # Progress bars
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── conversion_worker.py
│   │   ├── download_worker.py
│   │   └── catalog_worker.py
│   └── utils/
│       ├── __init__.py
│       ├── paths.py
│       └── config.py
├── tests/gui/                  # GUI unit tests
├── requirements-gui.txt
└── docs/
    └── implementation_plan.md  # This file
```

## Implementation Phases

### Phase 1: Core Infrastructure (Complete)
**Issue**: [#3](https://github.com/tigger04/make-audiobook/issues/3) - Closed

- Project structure and dependencies
- Data models (Voice, VoiceCatalog, ConversionJob)
- Path utilities and configuration

### Phase 2: Background Workers (Complete)
**Issue**: [#4](https://github.com/tigger04/make-audiobook/issues/4) - Closed

- CatalogWorker - fetch/cache voices.json
- DownloadWorker - voice download with progress
- ConversionWorker - QProcess wrapper for make-audiobook

### Phase 3: UI Components (Complete)
**Issue**: [#5](https://github.com/tigger04/make-audiobook/issues/5) - Closed

- FileListWidget - drag-drop file input
- VoiceBrowserDialog - HuggingFace catalog browser
- VoiceManagerWidget - installed voice management
- SettingsPanel - conversion options
- ProgressPanel - progress display

### Phase 4: Main Window Integration (Complete)
**Issue**: [#6](https://github.com/tigger04/make-audiobook/issues/6) - Closed

- MainWindow assembly with tabs
- Menu bar and status bar
- Application entry points
- Configuration persistence

### Phase 5: Packaging (Complete)
**Issue**: [#2](https://github.com/tigger04/make-audiobook/issues/2)

- macOS: .app bundle via py2app, distributed as DMG and Homebrew cask
- Homebrew tap: `brew install --cask tigger04/tap/make-audiobook`
- Linux/Windows: documented in installation guide

## Dependencies

### Python Packages
```
# requirements-gui.txt
PySide6>=6.6.0
requests>=2.31.0

# dev
pytest>=7.0.0
pytest-qt>=4.2.0
```

### System Dependencies
Checked at runtime (existing requirements):
- piper (via pipx)
- ffmpeg
- pandoc

## Key Interfaces

### Voice Model
```python
@dataclass
class Voice:
    key: str           # e.g., "en_US-ryan-high"
    name: str          # e.g., "Ryan"
    language: str      # e.g., "en_US"
    quality: str       # "low", "medium", "high"
    files: dict        # {".onnx": {...}, ".onnx.json": {...}}
    size_bytes: int
    installed: bool = False
```

### Worker Signals
```python
# CatalogWorker
catalogReady = Signal(VoiceCatalog)
error = Signal(str)

# DownloadWorker
progress = Signal(int)      # percent
finished = Signal(bool)     # success
error = Signal(str)

# ConversionWorker
progress = Signal(str, int) # filename, percent
finished = Signal(str, bool) # filename, success
log = Signal(str)
```

## Testing Strategy

- **Unit tests**: Models, workers (mocked I/O) — 264 tests passing
- **Widget tests**: pytest-qt for all UI components (file list, settings, voice browser, voice manager, progress panel, main window)
- **Integration tests**: Full flow with mocked subprocess
- **Manual testing**: Documented checklist per issue

## Issue Dependency Graph

```
#1 (GUI interface - parent)
├── #3 (Core infrastructure) ✓
│   └── #4 (Workers) ✓
│       └── #5 (UI components) ✓
│           └── #6 (Main window) ✓
├── #2 (Installers) ✓
└── #21 (WhisperSpeech TTS) - Phase 1 ✓
```

## Notes

- Follow TDD per project standards
- Use PySide6 (LGPL) not PyQt6 (GPL)
- Target macOS and Linux primarily
- Bash script interface is stable - avoid modifying output format
