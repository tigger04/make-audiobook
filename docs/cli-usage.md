# CLI Usage Guide

The `make-audiobook` command-line interface provides powerful batch conversion capabilities for converting documents to audiobooks using Piper TTS.

## Basic Usage

```bash
# Convert a single file (interactive voice selection)
make-audiobook mybook.txt

# Convert multiple files
make-audiobook chapter1.txt chapter2.txt chapter3.txt

# Convert using wildcards
make-audiobook chapter*.md
```

## Options

| Option | Description |
|--------|-------------|
| `-h`, `--help` | Show help message |
| `-r`, `--random-voice` | Use a random voice for each file |
| `-r=FILTER`, `--random=FILTER` | Use a random voice filtered by quality (high, medium, low) |
| `-l`, `--list-voices` | List all installed voices |
| `-u`, `--update-voices` | Update installed Piper voices |
| `-s=SCALE`, `--length_scale=SCALE` | Set speech speed (higher = slower). Default: 1.5 |

## Examples

### Interactive Voice Selection

When no voice option is specified, you'll be prompted to select a voice interactively using fzf:

```bash
make-audiobook mybook.epub
```

### Random Voice

Use a random voice from your installed voices:

```bash
make-audiobook mybook.epub --random-voice
```

Filter random selection by quality:

```bash
# Only use high-quality voices
make-audiobook mybook.epub --random=high

# Only use medium-quality voices
make-audiobook chapter*.docx --random=medium
```

### Adjusting Speed

The `length_scale` parameter controls speech speed. Higher values = slower speech.

```bash
# Slower speech (good for complex content)
make-audiobook mybook.txt --length_scale=2.0

# Faster speech
make-audiobook mybook.txt -s=1.0

# Default is 1.5
make-audiobook mybook.txt
```

### Batch Processing

Process multiple files at once:

```bash
# Multiple specific files
make-audiobook chapter1.md chapter2.md chapter3.md

# Wildcard matching
make-audiobook "The Great Gatsby"/*.txt

# All supported files in a directory
make-audiobook *.epub *.txt *.docx
```

## Supported Input Formats

- `.txt` - Plain text
- `.epub` - EPUB ebooks
- `.docx` - Microsoft Word documents
- `.md` - Markdown
- `.html` - HTML pages
- `.pdf` - PDF documents

## Voice Management

### List Installed Voices

```bash
make-audiobook --list-voices
```

Output shows each voice with language flag and quality rating:
```
🇬🇧 en_GB-alan-medium ⭐️⭐️
🇺🇸 en_US-ryan-high ⭐️⭐️⭐️
🇺🇸 en_US-libritts_r-medium ⭐️⭐️
```

### Install Voices

Run the voice setup script to install voices:

```bash
piper-voices-setup
```

This installs a curated set of high-quality English voices. For other languages or additional voices, visit the [Piper Voices repository](https://huggingface.co/rhasspy/piper-voices).

### Update Voices

Update all installed voices to latest versions:

```bash
make-audiobook --update-voices
```

## Metadata (ID3 Tags)

You'll be prompted for author and book title during conversion. These are embedded as ID3 tags in the output MP3 files.

```
Author: Jane Austen
Book Title: Pride and Prejudice
```

Track numbers are automatically calculated from filenames when processing multiple files.

## Output

Output files are created in the same directory as the input files with `.mp3` extension:

```
mybook.txt → mybook.mp3
chapter01.epub → chapter01.mp3
```

## First Run

On first run, if no Piper voices are found, the script will prompt you to run `piper-voices-setup` to download voices.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (missing dependencies, conversion failed, etc.) |
| 2 | Usage error (invalid arguments) |

## See Also

- [Installation Guide](installation.md)
- [GUI Usage Guide](gui-usage.md)
- [Project Vision](vision.md)
