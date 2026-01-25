# Installation Guide

## Requirements

Before installing, ensure your input files are **DRM-free**. This tool cannot process DRM-protected ebooks (Kindle .azw, Adobe DRM .epub, etc.).

---

## macOS

### Homebrew (Recommended)

```bash
# Install the GUI application (includes CLI)
brew install --cask tigger04/tap/make-audiobook

# Or CLI-only (no GUI)
brew install tigger04/tap/make-audiobook
```

The cask installs the full GUI application with all dependencies bundled. The formula installs CLI tools only (requires ffmpeg, pandoc, piper-tts, fzf, fd).

### Manual Installation

1. Install Homebrew from https://brew.sh if not already installed

2. Clone and run the installer:
   ```bash
   git clone --recursive https://github.com/tigger04/make-audiobook
   cd make-audiobook
   ./install-dependencies
   ```

3. Install voices on first run, or manually:
   ```bash
   ./piper-voices-setup
   ```

4. For the GUI, install Python dependencies:
   ```bash
   make install-gui
   make gui
   ```

---

## Linux

### Debian / Ubuntu (apt)

```bash
# Add the repository
sudo add-apt-repository ppa:tigger04/make-audiobook
sudo apt update

# Install
sudo apt install make-audiobook
```

### NixOS / Nix

Add to your `flake.nix`:

```nix
{
  inputs.make-audiobook.url = "github:tigger04/make-audiobook";

  # In your system configuration or home-manager:
  environment.systemPackages = [ inputs.make-audiobook.packages.${system}.default ];
}
```

Or run directly without installing:

```bash
nix run github:tigger04/make-audiobook
```

### AppImage (Universal Linux)

Download the AppImage from the [releases page](https://github.com/tigger04/make-audiobook/releases):

```bash
wget https://github.com/tigger04/make-audiobook/releases/latest/download/make-audiobook.AppImage
chmod +x make-audiobook.AppImage
./make-audiobook.AppImage
```

### Manual Installation

1. Install system dependencies:
   ```bash
   # Debian/Ubuntu
   sudo apt install ffmpeg pandoc fzf fd-find python3 python3-pip python3-venv

   # Fedora
   sudo dnf install ffmpeg pandoc fzf fd-find python3 python3-pip

   # Arch
   sudo pacman -S ffmpeg pandoc fzf fd python python-pip
   ```

2. Install piper-tts:
   ```bash
   pip install --user piper-tts
   # Ensure ~/.local/bin is in your PATH
   ```

3. Clone and set up:
   ```bash
   git clone --recursive https://github.com/tigger04/make-audiobook
   cd make-audiobook
   ./piper-voices-setup
   ```

4. For the GUI:
   ```bash
   make install-gui
   make gui
   ```

---

## Windows

### Installer (Recommended)

Download the installer from the [releases page](https://github.com/tigger04/make-audiobook/releases):

1. Run `make-audiobook-setup.exe`
2. Follow the installation wizard
3. Launch from Start Menu or run `make-audiobook` from Command Prompt

### Manual Installation

1. Install dependencies via winget:
   ```powershell
   winget install ffmpeg
   winget install pandoc
   winget install Python.Python.3.12
   ```

2. Install piper-tts:
   ```powershell
   pip install piper-tts
   ```

3. Download or clone the repository:
   ```powershell
   git clone --recursive https://github.com/tigger04/make-audiobook
   cd make-audiobook
   ```

4. Run via Python:
   ```powershell
   # CLI
   python make-audiobook mybook.epub

   # GUI
   pip install -r requirements-gui.txt
   python -m gui
   ```

---

## Post-Installation

### Voice Setup

On first run, you'll be prompted to install voices. Alternatively, run:

```bash
./piper-voices-setup
```

This installs a curated set of high-quality English (US and GB) voices. For other languages, use the GUI's voice browser or edit `piper-voices-setup`.

### Verify Installation

```bash
# Check CLI
make-audiobook --help

# Check dependencies
which piper ffmpeg pandoc
```

### Launch GUI

```bash
# Via make
make gui

# Or directly
./make-audiobook-gui

# Or as Python module
python -m gui
```

---

## Troubleshooting

### "piper not found"

Ensure piper is in your PATH:
```bash
# Check installation location
pip show piper-tts

# Add to PATH if needed (Linux/macOS)
export PATH="$HOME/.local/bin:$PATH"
```

### "ffmpeg not found" / "pandoc not found"

Install via your package manager:
```bash
# macOS
brew install ffmpeg pandoc

# Debian/Ubuntu
sudo apt install ffmpeg pandoc
```

### GUI won't start

Ensure PySide6 is installed:
```bash
pip install PySide6
# Or use make
make install-gui
```

### DRM-protected files fail

This tool only works with DRM-free files. Convert your files using Calibre or obtain DRM-free versions.
