# CLI Usage Guide

The `make-audiobook` command converts documents to audiobooks using Kokoro (recommended) or Piper TTS. Kokoro produces remarkably natural speech; Piper offers faster processing with 100+ voice options.

## Basic Usage

```bash
# Kokoro engine (default) — natural-sounding, chapter-aware
make-audiobook mybook.epub

# Kokoro with specific voice and speed
make-audiobook mybook.epub --voice=af_bella --speed=1.2

# Piper engine — fast, interactive voice selection
make-audiobook mybook.txt --engine=piper

# Batch processing
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
| `--engine=ENGINE` | TTS engine: kokoro (default), piper, whisperspeech |
| `--speed=SPEED` | Speed multiplier for Kokoro (1.0 = normal, 1.5 = faster) |

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

### Kokoro Engine (Recommended)

Kokoro produces the most natural-sounding speech available in open-source TTS. It natively handles epub and pdf with chapter detection, and outputs MP3 directly without intermediate conversion steps.

```bash
# Convert with Kokoro (default engine, uses voice af_heart)
make-audiobook mybook.epub

# Specify a Kokoro voice
make-audiobook mybook.epub --voice=af_bella

# Adjust Kokoro speed (1.0 = normal, higher = faster)
make-audiobook mybook.epub --speed=1.2

# Chapter-aware pdf conversion
make-audiobook mybook.pdf --voice=bm_lewis
```

Kokoro has 26 built-in voices. Model files (~700 MB) are downloaded automatically on first use. Kokoro and its dependency `espeak-ng` are installed automatically — see [Installation Guide](installation.md#kokoro-tts-engine-default).

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
- `.epub` - EPUB ebooks (chapter-aware with Kokoro)
- `.docx` - Microsoft Word documents
- `.md` - Markdown
- `.html` - HTML pages
- `.pdf` - PDF documents (chapter-aware with Kokoro)
- `.mobi` - Mobipocket ebooks (requires Calibre)

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

Kokoro is the default engine and requires no voice download — its 26 voices are built in. If you switch to the Piper engine and no voices are found, the script will prompt you to run `piper-voices-setup` to download voices.

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
