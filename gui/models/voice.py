# ABOUTME: Data models for Piper TTS voices and the voice catalog.
# ABOUTME: Handles parsing of HuggingFace voices.json and filtering/search.

"""Voice and VoiceCatalog data models."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Voice:
    """Represents a single Piper TTS voice.

    Attributes:
        key: Unique identifier (e.g., "en_US-ryan-high")
        name: Human-readable name (e.g., "Ryan")
        language: Language code (e.g., "en_US")
        quality: Quality level ("low", "medium", "high")
        files: Dictionary of file metadata (size, checksum)
        size_bytes: Total size of all voice files
        installed: Whether the voice is installed locally
    """

    key: str
    name: str
    language: str
    quality: str
    files: dict
    size_bytes: int
    installed: bool = False


@dataclass
class VoiceCatalog:
    """Collection of voices with filtering and lookup capabilities.

    Parses the HuggingFace Piper voices.json format and provides
    methods for filtering by language, quality, and installed status.
    """

    voices: list[Voice] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> VoiceCatalog:
        """Parse a voices.json dictionary into a VoiceCatalog.

        The voices.json structure is:
        {
            "en_US": {
                "ryan": {
                    "high": { "key": "en_US-ryan-high", ... },
                    "medium": { "key": "en_US-ryan-medium", ... }
                }
            }
        }
        """
        voices = []

        for lang_code, speakers in data.items():
            for speaker_name, qualities in speakers.items():
                for quality_level, voice_data in qualities.items():
                    # Calculate total size from all files
                    total_size = sum(
                        file_info.get("size_bytes", 0)
                        for file_info in voice_data.get("files", {}).values()
                    )

                    # Normalise files dict to use simple extensions as keys
                    files = {}
                    for filename, file_info in voice_data.get("files", {}).items():
                        if filename.endswith(".onnx.json"):
                            files[".onnx.json"] = file_info
                        elif filename.endswith(".onnx"):
                            files[".onnx"] = file_info

                    voice = Voice(
                        key=voice_data.get("key", f"{lang_code}-{speaker_name}-{quality_level}"),
                        name=voice_data.get("name", speaker_name.title()),
                        language=lang_code,
                        quality=quality_level,
                        files=files,
                        size_bytes=total_size,
                    )
                    voices.append(voice)

        return cls(voices=voices)

    @classmethod
    def from_json_string(cls, json_str: str) -> VoiceCatalog:
        """Parse a JSON string into a VoiceCatalog."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def filter_by_language(self, language: str) -> list[Voice]:
        """Return voices matching the given language code."""
        return [v for v in self.voices if v.language == language]

    def filter_by_quality(self, quality: str) -> list[Voice]:
        """Return voices matching the given quality level."""
        return [v for v in self.voices if v.quality == quality]

    def filter(
        self,
        language: Optional[str] = None,
        quality: Optional[str] = None,
        installed: Optional[bool] = None,
    ) -> list[Voice]:
        """Return voices matching all provided criteria."""
        result = self.voices

        if language is not None:
            result = [v for v in result if v.language == language]

        if quality is not None:
            result = [v for v in result if v.quality == quality]

        if installed is not None:
            result = [v for v in result if v.installed == installed]

        return result

    def get_by_key(self, key: str) -> Optional[Voice]:
        """Look up a voice by its unique key."""
        for voice in self.voices:
            if voice.key == key:
                return voice
        return None

    def get_languages(self) -> list[str]:
        """Return sorted list of unique language codes."""
        return sorted(set(v.language for v in self.voices))

    def get_qualities(self) -> list[str]:
        """Return sorted list of unique quality levels."""
        return sorted(set(v.quality for v in self.voices))

    def update_installed_status(self, voices_dir: Path) -> None:
        """Update installed status by checking filesystem.

        Voices are stored in: voices_dir/{language}/{voice_key}/{voice_key}.onnx
        """
        for voice in self.voices:
            # Expected path: voices_dir/en_US/en_US-ryan-high/en_US-ryan-high.onnx
            voice_path = voices_dir / voice.language / voice.key / f"{voice.key}.onnx"
            voice.installed = voice_path.exists()

    def get_installed_voices(self) -> list[Voice]:
        """Return only installed voices."""
        return [v for v in self.voices if v.installed]
