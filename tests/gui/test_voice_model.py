# ABOUTME: Tests for Voice and VoiceCatalog data models.
# ABOUTME: Verifies voice parsing, catalog filtering, and installed status detection.

"""Tests for Voice and VoiceCatalog models."""

import json
import pytest
from pathlib import Path

from gui.models.voice import Voice, VoiceCatalog


class TestVoice:
    """Tests for the Voice dataclass."""

    def test_voice_creation_with_required_fields(self):
        """Test Voice can be created with required fields."""
        voice = Voice(
            key="en_US-ryan-high",
            name="Ryan",
            language="en_US",
            quality="high",
            files={
                ".onnx": {"size_bytes": 100000, "md5_digest": "abc123"},
                ".onnx.json": {"size_bytes": 1000, "md5_digest": "def456"},
            },
            size_bytes=101000,
        )
        assert voice.key == "en_US-ryan-high"
        assert voice.name == "Ryan"
        assert voice.language == "en_US"
        assert voice.quality == "high"
        assert voice.size_bytes == 101000
        assert voice.installed is False

    def test_voice_installed_defaults_to_false(self):
        """Test Voice.installed defaults to False."""
        voice = Voice(
            key="en_GB-alba-medium",
            name="Alba",
            language="en_GB",
            quality="medium",
            files={},
            size_bytes=50000,
        )
        assert voice.installed is False

    def test_voice_can_be_marked_as_installed(self):
        """Test Voice can be created with installed=True."""
        voice = Voice(
            key="en_US-amy-low",
            name="Amy",
            language="en_US",
            quality="low",
            files={},
            size_bytes=25000,
            installed=True,
        )
        assert voice.installed is True

    def test_voice_language_code_extraction(self):
        """Test language code is correctly extracted."""
        voice = Voice(
            key="de_DE-thorsten-high",
            name="Thorsten",
            language="de_DE",
            quality="high",
            files={},
            size_bytes=100000,
        )
        assert voice.language == "de_DE"

    def test_voice_quality_levels(self):
        """Test all quality levels are valid."""
        for quality in ["low", "medium", "high"]:
            voice = Voice(
                key=f"en_US-test-{quality}",
                name="Test",
                language="en_US",
                quality=quality,
                files={},
                size_bytes=10000,
            )
            assert voice.quality == quality


class TestVoiceCatalog:
    """Tests for the VoiceCatalog class."""

    @pytest.fixture
    def sample_voices_json(self) -> dict:
        """Sample voices.json structure from HuggingFace."""
        return {
            "en_US": {
                "ryan": {
                    "high": {
                        "key": "en_US-ryan-high",
                        "name": "Ryan",
                        "language": {"code": "en_US", "family": "en", "region": "US"},
                        "quality": "high",
                        "num_speakers": 1,
                        "speaker_id_map": {},
                        "files": {
                            "en_US-ryan-high.onnx": {
                                "size_bytes": 63201294,
                                "md5_digest": "abc123",
                            },
                            "en_US-ryan-high.onnx.json": {
                                "size_bytes": 5039,
                                "md5_digest": "def456",
                            },
                        },
                    },
                    "medium": {
                        "key": "en_US-ryan-medium",
                        "name": "Ryan",
                        "language": {"code": "en_US", "family": "en", "region": "US"},
                        "quality": "medium",
                        "num_speakers": 1,
                        "speaker_id_map": {},
                        "files": {
                            "en_US-ryan-medium.onnx": {
                                "size_bytes": 17686654,
                                "md5_digest": "ghi789",
                            },
                            "en_US-ryan-medium.onnx.json": {
                                "size_bytes": 5041,
                                "md5_digest": "jkl012",
                            },
                        },
                    },
                },
                "amy": {
                    "low": {
                        "key": "en_US-amy-low",
                        "name": "Amy",
                        "language": {"code": "en_US", "family": "en", "region": "US"},
                        "quality": "low",
                        "num_speakers": 1,
                        "speaker_id_map": {},
                        "files": {
                            "en_US-amy-low.onnx": {
                                "size_bytes": 5000000,
                                "md5_digest": "mno345",
                            },
                            "en_US-amy-low.onnx.json": {
                                "size_bytes": 2000,
                                "md5_digest": "pqr678",
                            },
                        },
                    },
                },
            },
            "en_GB": {
                "alba": {
                    "medium": {
                        "key": "en_GB-alba-medium",
                        "name": "Alba",
                        "language": {"code": "en_GB", "family": "en", "region": "GB"},
                        "quality": "medium",
                        "num_speakers": 1,
                        "speaker_id_map": {},
                        "files": {
                            "en_GB-alba-medium.onnx": {
                                "size_bytes": 17000000,
                                "md5_digest": "stu901",
                            },
                            "en_GB-alba-medium.onnx.json": {
                                "size_bytes": 4000,
                                "md5_digest": "vwx234",
                            },
                        },
                    },
                },
            },
            "de_DE": {
                "thorsten": {
                    "high": {
                        "key": "de_DE-thorsten-high",
                        "name": "Thorsten",
                        "language": {"code": "de_DE", "family": "de", "region": "DE"},
                        "quality": "high",
                        "num_speakers": 1,
                        "speaker_id_map": {},
                        "files": {
                            "de_DE-thorsten-high.onnx": {
                                "size_bytes": 60000000,
                                "md5_digest": "yza567",
                            },
                            "de_DE-thorsten-high.onnx.json": {
                                "size_bytes": 5000,
                                "md5_digest": "bcd890",
                            },
                        },
                    },
                },
            },
        }

    def test_catalog_from_dict_parses_all_voices(self, sample_voices_json):
        """Test VoiceCatalog.from_dict parses all voices correctly."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        assert len(catalog.voices) == 5

    def test_catalog_voices_have_correct_keys(self, sample_voices_json):
        """Test parsed voices have correct keys."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        keys = {v.key for v in catalog.voices}
        expected_keys = {
            "en_US-ryan-high",
            "en_US-ryan-medium",
            "en_US-amy-low",
            "en_GB-alba-medium",
            "de_DE-thorsten-high",
        }
        assert keys == expected_keys

    def test_catalog_filter_by_language(self, sample_voices_json):
        """Test filtering voices by language code."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        en_us_voices = catalog.filter_by_language("en_US")
        assert len(en_us_voices) == 3
        assert all(v.language == "en_US" for v in en_us_voices)

    def test_catalog_filter_by_quality(self, sample_voices_json):
        """Test filtering voices by quality level."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        high_voices = catalog.filter_by_quality("high")
        assert len(high_voices) == 2
        assert all(v.quality == "high" for v in high_voices)

    def test_catalog_filter_by_language_and_quality(self, sample_voices_json):
        """Test filtering voices by both language and quality."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        filtered = catalog.filter(language="en_US", quality="medium")
        assert len(filtered) == 1
        assert filtered[0].key == "en_US-ryan-medium"

    def test_catalog_filter_returns_empty_for_no_match(self, sample_voices_json):
        """Test filter returns empty list when no matches."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        filtered = catalog.filter(language="fr_FR")
        assert len(filtered) == 0

    def test_catalog_get_by_key(self, sample_voices_json):
        """Test getting a voice by its key."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        voice = catalog.get_by_key("en_US-ryan-high")
        assert voice is not None
        assert voice.name == "Ryan"
        assert voice.quality == "high"

    def test_catalog_get_by_key_returns_none_for_unknown(self, sample_voices_json):
        """Test get_by_key returns None for unknown key."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        voice = catalog.get_by_key("nonexistent-voice")
        assert voice is None

    def test_catalog_get_languages(self, sample_voices_json):
        """Test getting unique language codes."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        languages = catalog.get_languages()
        assert languages == sorted(["de_DE", "en_GB", "en_US"])

    def test_catalog_get_qualities(self, sample_voices_json):
        """Test getting unique quality levels."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        qualities = catalog.get_qualities()
        assert qualities == ["high", "low", "medium"]

    def test_catalog_update_installed_status(self, sample_voices_json, tmp_path):
        """Test updating installed status based on filesystem."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)

        # Create a fake voices directory with one installed voice
        voices_dir = tmp_path / "piper" / "voices" / "en_US" / "en_US-ryan-high"
        voices_dir.mkdir(parents=True)
        (voices_dir / "en_US-ryan-high.onnx").touch()
        (voices_dir / "en_US-ryan-high.onnx.json").touch()

        catalog.update_installed_status(tmp_path / "piper" / "voices")

        ryan_high = catalog.get_by_key("en_US-ryan-high")
        ryan_medium = catalog.get_by_key("en_US-ryan-medium")

        assert ryan_high.installed is True
        assert ryan_medium.installed is False

    def test_catalog_get_installed_voices(self, sample_voices_json, tmp_path):
        """Test getting only installed voices."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)

        # Create fake installed voices
        for voice_key in ["en_US-ryan-high", "en_GB-alba-medium"]:
            lang = voice_key.split("-")[0]
            voice_dir = tmp_path / "piper" / "voices" / lang / voice_key
            voice_dir.mkdir(parents=True)
            (voice_dir / f"{voice_key}.onnx").touch()

        catalog.update_installed_status(tmp_path / "piper" / "voices")
        installed = catalog.get_installed_voices()

        assert len(installed) == 2
        assert all(v.installed for v in installed)

    def test_catalog_voice_size_calculation(self, sample_voices_json):
        """Test voice size is sum of all file sizes."""
        catalog = VoiceCatalog.from_dict(sample_voices_json)
        ryan_high = catalog.get_by_key("en_US-ryan-high")
        # 63201294 + 5039 = 63206333
        assert ryan_high.size_bytes == 63201294 + 5039

    def test_catalog_empty_dict(self):
        """Test VoiceCatalog handles empty dict."""
        catalog = VoiceCatalog.from_dict({})
        assert len(catalog.voices) == 0

    def test_catalog_from_json_string(self, sample_voices_json):
        """Test VoiceCatalog.from_json_string parses JSON correctly."""
        json_str = json.dumps(sample_voices_json)
        catalog = VoiceCatalog.from_json_string(json_str)
        assert len(catalog.voices) == 5
