# GUI Usage Guide

The make-audiobook GUI provides a visual interface for converting documents to audiobooks, with built-in voice management.

## Launching the GUI

### macOS Gatekeeper Warning

On first launch, macOS may show: "Apple could not verify make-audiobook.app is free of malware..."

This happens because the app is not notarized (Apple's code-signing service). To bypass this:

**Option 1: Right-click to open (easiest)**
1. Right-click (or Control+click) on make-audiobook.app
2. Select "Open" from the context menu
3. Click "Open" in the dialog that appears
4. The app will launch and be remembered for future launches

**Option 2: Remove quarantine attribute**
```bash
xattr -cr /Applications/make-audiobook.app
```

**Option 3: Install via Homebrew**

Installing via Homebrew cask bypasses Gatekeeper:
```bash
brew install --cask tigger04/tap/make-audiobook
```

### macOS (Homebrew)

If installed via Homebrew cask:
- Open from Applications folder, or
- Run from terminal: `open -a make-audiobook`

### From Source

```bash
# Using make
make gui

# Using the launcher script
./make-audiobook-gui

# Using Python directly
python -m gui
```

## Interface Overview

The GUI has two main tabs:

1. **Convert** - Add files and convert them to audiobooks
2. **Voices** - Manage installed voices

## Convert Tab

### Adding Files

You can add files in three ways:

1. **Drag and drop** - Drag files from Finder directly onto the file list
2. **Add Files button** - Click "Add Files..." to open a file picker
3. **File menu** - Use File → Open Files...

Supported formats: `.txt`, `.epub`, `.docx`, `.md`, `.html`, `.pdf`

### Managing the File List

- **Remove** - Select files and click "Remove" to remove them from the list
- **Clear All** - Remove all files from the list
- Files show filename and size

### Voice Settings

**Voice Selection**
- Select a specific installed voice from the dropdown
- Check "Use random voice" to have the app select a random voice for each file
- When random is enabled, optionally filter by quality (High, Medium, Low, or Any)

**Speed (Length Scale)**
- Adjust the slider to control speech speed
- Higher values = slower speech
- Default: 1.5x (slightly slower than normal, good for audiobooks)
- Range: 0.5x (fast) to 3.0x (very slow)

**Metadata (ID3 Tags)**
- Enter Author name (e.g., "Jane Austen")
- Enter Book Title (e.g., "Pride and Prejudice")
- These are embedded in the output MP3 files

### Converting

1. Add one or more files
2. Select a voice or enable random mode
3. Optionally adjust speed and enter metadata
4. Click "Convert to Audiobook"

The progress panel shows:
- Current file being processed
- Progress bar
- Log output from the conversion
- Cancel button to stop conversion

### Progress Panel

During conversion:
- Current file name displayed
- Progress bar shows conversion progress
- Log messages provide detailed status
- Click "Cancel" to stop the conversion

## Voices Tab

### Viewing Installed Voices

The Voices tab shows all currently installed voices with:
- Voice name
- Language
- Quality rating

### Installing New Voices

1. Click "Browse Voices..." to open the Voice Browser
2. Search and filter voices by:
   - **Search box** - Filter by name
   - **Language** - Filter by language (e.g., en_US, de_DE)
   - **Quality** - Filter by quality level (High, Medium, Low)
3. Select one or more voices (use Shift+Click or Cmd+Click for multiple)
4. Click "Download Selected"

Voices are downloaded from the [Piper Voices](https://huggingface.co/rhasspy/piper-voices) repository on HuggingFace.

### Deleting Voices

Select a voice in the list and click "Delete" to remove it. This frees disk space but you'll need to re-download if you want to use it again.

### Refreshing the Voice List

Click "Refresh" to rescan for installed voices. Use this if you've installed voices manually or via the CLI.

## Menu Bar

### File Menu

- **Open Files...** - Add files to convert
- **Exit** - Close the application

### Tools Menu

- **Update Voice Catalog** - Refresh the online voice catalog from HuggingFace

### Help Menu

- **About** - Show version and license information

## Status Bar

The status bar at the bottom shows:
- Number of installed voices
- Current operation status
- Download/conversion progress messages

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open Files | Cmd+O (macOS) / Ctrl+O |
| Quit | Cmd+Q (macOS) / Ctrl+Q |

## Configuration

Settings are automatically saved:
- Window position and size
- Last used speed setting
- Last selected voice

Configuration is stored in:
- macOS: `~/Library/Application Support/make-audiobook/config.json`
- Linux: `~/.config/make-audiobook/config.json`

## Troubleshooting

### GUI Won't Start

Ensure PySide6 is installed:
```bash
pip install PySide6
# Or use make
make install-gui
```

### No Voices Available

If the voice dropdown is empty:
1. Go to the Voices tab
2. Click "Browse Voices..."
3. Download at least one voice

Or run from terminal:
```bash
piper-voices-setup
```

### Conversion Fails

Check that all dependencies are installed:
```bash
which piper ffmpeg pandoc
```

See [Installation Guide](installation.md) for dependency installation.

### Files Not Accepted

Ensure your files are:
- DRM-free (this tool cannot process DRM-protected files)
- In a supported format (.txt, .epub, .docx, .md, .html, .pdf)

## See Also

- [Installation Guide](installation.md)
- [CLI Usage Guide](cli-usage.md)
- [Project Vision](vision.md)
