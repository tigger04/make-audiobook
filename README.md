# make-audiobook

Convert ebooks and documents into audiobooks using Piper TTS — locally, privately, and free.

**[Installation](./docs/installation.md)** | **[CLI Guide](./docs/cli-usage.md)** | **[GUI Guide](./docs/gui-usage.md)** | **[Vision](./docs/vision.md)**

## Important

Input files must be **DRM-free**. This tool cannot process DRM-protected ebooks (e.g., Kindle .azw, Adobe DRM .epub). Use DRM-free sources or legally remove DRM from files you own.

## Features

- **Local processing** — no cloud services, no data leaves your machine
- **GUI and CLI** interfaces
- Converts epub, docx, txt, md, html, pdf to MP3
- **Batch processing** multiple files
- **ID3 metadata** tagging (author, title, track numbers)
- **Voice browser** to download from 100+ Piper voices
- Interactive or random voice selection
- Adjustable speech speed

## Quickstart

### Install (macOS)

```bash
# GUI application (includes CLI)
brew install --cask tigger04/tap/make-audiobook

# CLI only
brew install tigger04/tap/make-audiobook
```

### Install (NixOS / Nix)

```bash
nix run github:tigger04/make-audiobook
```

See the [Installation Guide](./docs/installation.md) for Linux, Windows, and manual installation.

### GUI

Launch from Applications, or:

```bash
make gui
```

1. Drag files onto the window
2. Select a voice
3. Click "Convert to Audiobook"

[Full GUI Guide](./docs/gui-usage.md)

### CLI

```bash
# Convert with interactive voice selection
make-audiobook mybook.epub

# Random voice
make-audiobook mybook.epub --random-voice

# Batch processing with high-quality voices
make-audiobook chapter*.txt --random=high

# Adjust speed (higher = slower, default 1.5)
make-audiobook mybook.epub --length_scale=2.0
```

[Full CLI Guide](./docs/cli-usage.md)

## Supported Formats

| Input  | Output |
|--------|--------|
| .epub  | .mp3   |
| .docx  |        |
| .txt   |        |
| .md    |        |
| .html  |        |
| .pdf   |        |

## Dependencies

- [Piper TTS](https://github.com/rhasspy/piper) — neural text-to-speech
- [FFmpeg](https://ffmpeg.org/) — audio encoding
- [Pandoc](https://pandoc.org/) — document conversion
- [PySide6](https://doc.qt.io/qtforpython-6/) — GUI framework (LGPL)
- [fzf](https://github.com/junegunn/fzf) — interactive voice selection (CLI)
- [fd](https://github.com/sharkdp/fd) — fast file finder

## Make Targets

| Target | Description |
|--------|-------------|
| `make install` | Install CLI dependencies |
| `make install-gui` | Install GUI dependencies and default voices |
| `make gui` | Launch the GUI |
| `make test` | Run all tests |
| `make test-gui` | Run GUI tests |
| `make lint` | Run linters (Ruff, ShellCheck) |
| `make clean` | Remove build artefacts |
| `make release` | Tag, build, and push a release |
| `make help` | Show all targets |

## Project Structure

| Path | Description |
|------|-------------|
| `make-audiobook` | CLI executable (bash) |
| `make-audiobook-gui` | GUI launcher script |
| `piper-voices-setup` | Voice installation script |
| `gui/` | PySide6 GUI source code |
| `tests/gui/` | GUI test suite (264 tests) |
| `docs/` | Documentation |
| `homebrew/` | Homebrew formula and cask |
| `flake.nix` | Nix flake for NixOS/nix-darwin |
| `scripts/` | Build scripts (macOS .app bundle) |
| `resources/` | App icon and assets |
| `Makefile` | Build targets |

## Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](./docs/installation.md) | Setup for macOS, Linux, NixOS, Windows |
| [CLI Usage](./docs/cli-usage.md) | Command-line options and examples |
| [GUI Usage](./docs/gui-usage.md) | Visual interface walkthrough |
| [Project Vision](./docs/vision.md) | Goals and design philosophy |
| [Implementation Plan](./docs/implementation_plan.md) | GUI architecture and phasing |

## License

MIT — Copyright Tadhg Paul
