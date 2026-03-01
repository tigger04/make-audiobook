# Vision: make-audiobook

## Purpose

Convert ebooks and documents into high-quality audiobooks using local, open-source text-to-speech technology - no cloud services, no subscriptions, no data leaving your machine.

## Problem Statement

Audiobook creation is typically:
- **Expensive**: Commercial TTS services charge per character
- **Privacy-compromising**: Cloud services process your text on remote servers
- **Technically demanding**: Requires chaining multiple tools (conversion, TTS, encoding, tagging)
- **Limited**: Commercial options restrict voice selection and output formats

## Solution

make-audiobook provides a simple, local pipeline:

```
Kokoro engine (recommended):
  Document (epub, pdf, txt) → MP3 directly (Kokoro TTS, chapter-aware)
  Document (docx, md, html, mobi) → Plain text (pandoc) → MP3 (Kokoro TTS)

Piper engine (alternative — faster, more voice variety):
  Document (epub, docx, txt, md, html, pdf, mobi)
      → Plain text (pandoc)
      → Speech audio (Piper TTS)
      → MP3 with metadata (ffmpeg)
```

All processing happens locally using open-source tools. Users own their output.

## Core Principles

### 1. Local-First
All processing runs on your machine. No internet required after initial voice download. Your documents never leave your computer.

### 2. Open Source
Built entirely on FOSS:
- Kokoro TTS (Apache-2.0) - natural-sounding neural TTS (recommended)
- Piper TTS (MIT) - fast neural TTS with extensive voice library
- Pandoc (GPL) - universal document converter
- FFmpeg (LGPL) - audio encoding
- PySide6 (LGPL) - GUI framework

### 3. Simplicity
One command, one audiobook:
```bash
make-audiobook mybook.epub
```

### 4. Quality
Kokoro produces remarkably natural speech — closer to a human narrator than any other open-source TTS available. It is the recommended engine for audiobook conversion, with chapter-aware processing for epub and pdf. Piper offers a faster alternative with 100+ downloadable voices when speed or voice variety is preferred over naturalness.

### 5. Accessibility
The GUI removes technical barriers. Non-technical users can:
- Drag files and click Convert
- Browse and install voices visually
- See progress and results clearly

## Target Users

1. **Readers with visual impairments** who want to convert personal documents
2. **Commuters** who want to listen to articles, papers, or ebooks
3. **Authors** who want to preview their work as audio
4. **Language learners** who benefit from hearing text read aloud
5. **Anyone** who prefers listening to reading

## Non-Goals

- Real-time streaming TTS (we batch-process complete files)
- Voice cloning or custom voice training
- Commercial audiobook production (no chapter markers, no complex editing)
- Windows support as primary target (community contributions welcome)

## Roadmap

### v1.x (Complete)
- [x] CLI batch processing
- [x] Voice selection (interactive + random)
- [x] ID3 metadata tagging
- [x] Multiple input formats

### v2.x (Current)
- [x] GUI interface (#1)
- [x] In-app voice management
- [x] macOS Homebrew cask and formula (#15)
- [x] Nix flake (#10)
- [x] TTS engine abstraction - WhisperSpeech support (#21) - Phase 1
- [x] Kokoro TTS engine integration (#24) — high-quality TTS with chapter-aware epub/pdf
- [ ] Cross-platform installers - Linux/Windows (#2)

### Future Considerations
- Chapter detection and splitting
- Voice preview before conversion
- Pronunciation customisation (lexicons)
- Queue management for large batches
- Multiple output formats (m4b, opus)

## Success Metrics

- Users can convert a book without reading documentation
- Conversion completes without manual intervention
- Output quality suitable for extended listening
- Works offline after initial setup

## License

MIT License - use freely, modify freely, share freely.

Copyright Tadhg Paul
