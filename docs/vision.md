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
Document (epub, docx, txt, md, html, pdf)
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
- Piper TTS (MIT) - neural text-to-speech
- Pandoc (GPL) - universal document converter
- FFmpeg (LGPL) - audio encoding
- PySide6 (LGPL) - GUI framework

### 3. Simplicity
One command, one audiobook:
```bash
make-audiobook mybook.epub
```

### 4. Quality
Piper voices rival commercial TTS. Medium quality is production-ready; high quality is exceptional. Users choose their trade-off between speed and fidelity.

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

### Current (v1.x)
- [x] CLI batch processing
- [x] Voice selection (interactive + random)
- [x] ID3 metadata tagging
- [x] Multiple input formats

### Near-term (v2.x)
- [ ] GUI interface (#1)
- [ ] In-app voice management
- [ ] Cross-platform installers (#2)

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
