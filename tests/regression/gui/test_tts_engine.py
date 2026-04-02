# ABOUTME: Unit tests for TTSEngine abstraction and implementations.
# ABOUTME: Tests the interface contract and engine-specific behavior.

"""Tests for TTS engine abstraction."""

import tempfile
from abc import ABC
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gui.models.tts_engine import (
    TTSEngine,
    PiperEngine,
    WhisperSpeechEngine,
    KokoroEngine,
    EngineNotAvailableError,
)
from gui.models.voice import Voice


class TestTTSEngineInterface:
    """Test the abstract TTSEngine interface."""

    def test_ttsengine_is_abstract_base_class(self):
        """TTSEngine should be an abstract base class."""
        assert issubclass(TTSEngine, ABC)

    def test_ttsengine_requires_name_property(self):
        """TTSEngine should require a name property."""
        # Create a concrete implementation without name property implementation
        # This should fail at instantiation since name is abstract
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            class BadEngine(TTSEngine):
                # Missing the @property name method
                def is_available(self):
                    return True

                def synthesize(self, text, voice, output_path, **kwargs):
                    pass

                def get_voices(self):
                    return []

            BadEngine()

    def test_ttsengine_requires_synthesize_method(self):
        """TTSEngine should require a synthesize method."""
        # Create a concrete implementation without synthesize
        class BadEngine(TTSEngine):
            @property
            def name(self):
                return "bad"

            def is_available(self):
                return True

            def get_voices(self):
                return []

        # Should not be instantiable
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BadEngine()

    def test_ttsengine_requires_is_available_method(self):
        """TTSEngine should require an is_available method."""
        # Create a concrete implementation without is_available
        class BadEngine(TTSEngine):
            @property
            def name(self):
                return "bad"

            def synthesize(self, text, voice, output_path, **kwargs):
                pass

            def get_voices(self):
                return []

        # Should not be instantiable
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BadEngine()

    def test_ttsengine_requires_get_voices_method(self):
        """TTSEngine should require a get_voices method."""
        # Create a concrete implementation without get_voices
        class BadEngine(TTSEngine):
            @property
            def name(self):
                return "bad"

            def is_available(self):
                return True

            def synthesize(self, text, voice, output_path, **kwargs):
                pass

        # Should not be instantiable
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BadEngine()


class TestPiperEngine:
    """Test the PiperEngine implementation."""

    @pytest.fixture
    def piper_engine(self):
        """Create a PiperEngine instance."""
        return PiperEngine()

    @pytest.fixture
    def sample_voice(self):
        """Create a sample Piper voice."""
        return Voice(
            key="en_US-ryan-high",
            name="Ryan",
            language="en_US",
            quality="high",
            engine="piper",
            files={
                ".onnx": {"size_bytes": 63201980},
                ".onnx.json": {"size_bytes": 548},
            },
            size_bytes=63202528,
            installed=True,
        )

    def test_piper_engine_name(self, piper_engine):
        """PiperEngine should have correct name."""
        assert piper_engine.name == "piper"

    @patch("gui.models.tts_engine.shutil.which")
    def test_piper_engine_is_available_when_installed(self, mock_which, piper_engine):
        """PiperEngine should be available when piper is installed."""
        mock_which.return_value = "/usr/local/bin/piper"
        assert piper_engine.is_available() is True
        mock_which.assert_called_once_with("piper")

    @patch("gui.models.tts_engine.shutil.which")
    def test_piper_engine_is_not_available_when_not_installed(
        self, mock_which, piper_engine
    ):
        """PiperEngine should not be available when piper is not installed."""
        mock_which.return_value = None
        assert piper_engine.is_available() is False

    @patch("gui.models.tts_engine.subprocess.run")
    @patch("gui.models.tts_engine.shutil.which")
    def test_piper_engine_synthesize_success(
        self, mock_which, mock_run, piper_engine, sample_voice
    ):
        """PiperEngine should synthesize text successfully."""
        mock_which.return_value = "/usr/local/bin/piper"
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.wav"
            text = "Hello, world!"

            piper_engine.synthesize(text, sample_voice, output_path)

            # Check subprocess was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "/usr/local/bin/piper"
            assert "--model" in call_args
            assert "--output-file" in call_args
            assert str(output_path) in call_args

    @patch("gui.models.tts_engine.subprocess.run")
    @patch("gui.models.tts_engine.shutil.which")
    def test_piper_engine_synthesize_with_length_scale(
        self, mock_which, mock_run, piper_engine, sample_voice
    ):
        """PiperEngine should pass length_scale parameter."""
        mock_which.return_value = "/usr/local/bin/piper"
        mock_run.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.wav"
            text = "Hello, world!"

            piper_engine.synthesize(
                text, sample_voice, output_path, length_scale=2.0
            )

            call_args = mock_run.call_args[0][0]
            assert "--length_scale" in call_args
            assert "2.0" in call_args

    @patch("gui.models.tts_engine.shutil.which")
    def test_piper_engine_synthesize_fails_when_not_available(
        self, mock_which, piper_engine, sample_voice
    ):
        """PiperEngine should raise error when not available."""
        mock_which.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.wav"
            text = "Hello, world!"

            with pytest.raises(EngineNotAvailableError, match="Piper is not installed"):
                piper_engine.synthesize(text, sample_voice, output_path)

    @patch("gui.models.tts_engine.VOICES_DIR")
    def test_piper_engine_get_voices(self, mock_voices_dir, piper_engine):
        """PiperEngine should return installed voices."""
        # Create mock Path objects
        mock_path1 = MagicMock()
        mock_path1.stem = "en_US-ryan-high"
        mock_path1.parent.parent.name = "en_US"
        mock_path1.stat.return_value = MagicMock(st_size=1000000)
        mock_path1.with_suffix.return_value.exists.return_value = True
        mock_path1.with_suffix.return_value.stat.return_value = MagicMock(st_size=500)

        mock_path2 = MagicMock()
        mock_path2.stem = "en_GB-alan-medium"
        mock_path2.parent.parent.name = "en_GB"
        mock_path2.stat.return_value = MagicMock(st_size=2000000)
        mock_path2.with_suffix.return_value.exists.return_value = False

        # Setup mock directory
        mock_voices_dir.exists.return_value = True
        mock_voices_dir.glob.return_value = [mock_path1, mock_path2]

        voices = piper_engine.get_voices()

        assert len(voices) == 2
        assert all(isinstance(v, Voice) for v in voices)
        assert voices[0].key == "en_GB-alan-medium"  # Sorted by language
        assert voices[0].engine == "piper"
        assert voices[1].key == "en_US-ryan-high"
        assert voices[1].engine == "piper"


class TestWhisperSpeechEngine:
    """Test the WhisperSpeechEngine implementation."""

    @pytest.fixture
    def whisper_engine(self):
        """Create a WhisperSpeechEngine instance."""
        return WhisperSpeechEngine()

    @pytest.fixture
    def sample_voice(self):
        """Create a sample WhisperSpeech voice."""
        return Voice(
            key="whisperspeech-default",
            name="Default",
            language="en",
            quality="high",
            engine="whisperspeech",
            files={},
            size_bytes=0,
            installed=True,
        )

    def test_whisperspeech_engine_name(self, whisper_engine):
        """WhisperSpeechEngine should have correct name."""
        assert whisper_engine.name == "whisperspeech"

    @patch("gui.models.tts_engine.importlib.util.find_spec")
    def test_whisperspeech_engine_is_available_when_installed(
        self, mock_find_spec, whisper_engine
    ):
        """WhisperSpeechEngine should be available when package is installed."""
        mock_find_spec.return_value = MagicMock()  # Non-None means found
        assert whisper_engine.is_available() is True
        mock_find_spec.assert_called_once_with("whisperspeech")

    @patch("gui.models.tts_engine.importlib.util.find_spec")
    def test_whisperspeech_engine_is_not_available_when_not_installed(
        self, mock_find_spec, whisper_engine
    ):
        """WhisperSpeechEngine should not be available when package is not installed."""
        mock_find_spec.return_value = None
        assert whisper_engine.is_available() is False

    @pytest.mark.skip(reason="WhisperSpeech integration test requires actual package")
    @patch("gui.models.tts_engine.importlib.util.find_spec")
    def test_whisperspeech_engine_synthesize_success(
        self, mock_find_spec, whisper_engine, sample_voice
    ):
        """WhisperSpeechEngine should synthesize text successfully."""
        # This test is skipped as it requires actual WhisperSpeech installation
        # The interface contract is tested by the abstract base class tests
        pass

    @patch("gui.models.tts_engine.importlib.util.find_spec")
    def test_whisperspeech_engine_synthesize_fails_when_not_available(
        self, mock_find_spec, whisper_engine, sample_voice
    ):
        """WhisperSpeechEngine should raise error when not available."""
        mock_find_spec.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.wav"
            text = "Hello, world!"

            with pytest.raises(
                EngineNotAvailableError, match="WhisperSpeech is not installed"
            ):
                whisper_engine.synthesize(text, sample_voice, output_path)

    def test_whisperspeech_engine_get_voices(self, whisper_engine):
        """WhisperSpeechEngine should return default voice."""
        voices = whisper_engine.get_voices()

        assert len(voices) == 1
        assert voices[0].key == "whisperspeech-default"
        assert voices[0].engine == "whisperspeech"
        assert voices[0].language == "en"


class TestTTSEngineSupportedFormats:
    """Test the supported_input_formats default behaviour."""

    def test_piper_engine_supported_formats_empty(self):
        """PiperEngine should return empty set for supported formats."""
        engine = PiperEngine()
        assert engine.supported_input_formats() == frozenset()

    def test_whisperspeech_engine_supported_formats_empty(self):
        """WhisperSpeechEngine should return empty set for supported formats."""
        engine = WhisperSpeechEngine()
        assert engine.supported_input_formats() == frozenset()


class TestKokoroEngine:
    """Test the KokoroEngine implementation."""

    @pytest.fixture
    def kokoro_engine(self):
        """Create a KokoroEngine instance."""
        return KokoroEngine()

    @pytest.fixture
    def sample_voice(self):
        """Create a sample Kokoro voice."""
        return Voice(
            key="af_heart",
            name="Heart",
            language="en",
            quality="high",
            engine="kokoro",
            files={},
            size_bytes=0,
            installed=True,
        )

    def test_kokoro_engine_name(self, kokoro_engine):
        """KokoroEngine should have correct name."""
        assert kokoro_engine.name == "kokoro"

    @patch("gui.models.tts_engine.shutil.which")
    def test_kokoro_engine_is_available_when_installed(self, mock_which, kokoro_engine):
        """KokoroEngine should be available when kokoro-tts and espeak-ng are installed."""
        mock_which.side_effect = lambda cmd: {
            "kokoro-tts": "/usr/local/bin/kokoro-tts",
            "espeak-ng": "/usr/local/bin/espeak-ng",
        }.get(cmd)
        assert kokoro_engine.is_available() is True

    @patch("gui.models.tts_engine.shutil.which")
    def test_kokoro_engine_not_available_without_kokoro_tts(self, mock_which, kokoro_engine):
        """KokoroEngine should not be available without kokoro-tts CLI."""
        mock_which.side_effect = lambda cmd: {
            "kokoro-tts": None,
            "espeak-ng": "/usr/local/bin/espeak-ng",
        }.get(cmd)
        assert kokoro_engine.is_available() is False

    @patch("gui.models.tts_engine.shutil.which")
    def test_kokoro_engine_not_available_without_espeak(self, mock_which, kokoro_engine):
        """KokoroEngine should not be available without espeak-ng."""
        mock_which.side_effect = lambda cmd: {
            "kokoro-tts": "/usr/local/bin/kokoro-tts",
            "espeak-ng": None,
        }.get(cmd)
        assert kokoro_engine.is_available() is False

    def test_kokoro_engine_supported_formats(self, kokoro_engine):
        """KokoroEngine should support epub, pdf, and txt natively."""
        formats = kokoro_engine.supported_input_formats()
        assert ".epub" in formats
        assert ".pdf" in formats
        assert ".txt" in formats

    def test_kokoro_engine_get_voices(self, kokoro_engine):
        """KokoroEngine should return built-in Kokoro voices."""
        voices = kokoro_engine.get_voices()
        assert len(voices) == 26
        assert all(isinstance(v, Voice) for v in voices)
        assert all(v.engine == "kokoro" for v in voices)
        # Check the recommended default voice exists
        voice_keys = [v.key for v in voices]
        assert "af_heart" in voice_keys

    def test_kokoro_engine_voices_have_correct_metadata(self, kokoro_engine):
        """KokoroEngine voices should have proper accent and type metadata."""
        voices = kokoro_engine.get_voices()
        # All should have language "en"
        assert all(v.language == "en" for v in voices)
        # Check sorting by key
        keys = [v.key for v in voices]
        assert keys == sorted(keys)

    @patch("gui.models.tts_engine.shutil.which")
    def test_kokoro_engine_synthesize_fails_when_not_available(
        self, mock_which, kokoro_engine, sample_voice
    ):
        """KokoroEngine should raise error when not available."""
        mock_which.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.mp3"
            with pytest.raises(
                EngineNotAvailableError, match="kokoro-tts is not installed"
            ):
                kokoro_engine.synthesize("Hello", sample_voice, output_path)

    def test_kokoro_engine_voices_have_gender_info(self, kokoro_engine):
        """KokoroEngine voices should encode gender in the quality field."""
        voices = kokoro_engine.get_voices()
        for v in voices:
            # Quality field used for gender/type info
            assert v.quality in ("female", "male")


class TestEngineRegistry:
    """Test the engine registry functionality."""

    def test_get_engine_by_name(self):
        """Should retrieve engine by name."""
        from gui.models.tts_engine import get_engine

        piper = get_engine("piper")
        assert isinstance(piper, PiperEngine)
        assert piper.name == "piper"

        whisper = get_engine("whisperspeech")
        assert isinstance(whisper, WhisperSpeechEngine)
        assert whisper.name == "whisperspeech"

        kokoro = get_engine("kokoro")
        assert isinstance(kokoro, KokoroEngine)
        assert kokoro.name == "kokoro"

    def test_get_engine_invalid_name_raises_error(self):
        """Should raise error for invalid engine name."""
        from gui.models.tts_engine import get_engine

        with pytest.raises(ValueError, match="Unknown engine: invalid"):
            get_engine("invalid")

    def test_get_available_engines(self):
        """Should return list of available engines."""
        from gui.models.tts_engine import get_available_engines

        with patch("gui.models.tts_engine.shutil.which") as mock_which:
            with patch("gui.models.tts_engine.importlib.util.find_spec") as mock_spec:
                # All engines available (shutil.which returns path for all)
                mock_which.return_value = "/usr/local/bin/piper"
                mock_spec.return_value = MagicMock()

                engines = get_available_engines()
                assert len(engines) == 3
                assert any(e.name == "piper" for e in engines)
                assert any(e.name == "whisperspeech" for e in engines)
                assert any(e.name == "kokoro" for e in engines)

                # Only Piper available (which returns path only for "piper")
                def piper_only(cmd):
                    if cmd == "piper":
                        return "/usr/local/bin/piper"
                    return None

                mock_which.side_effect = piper_only
                mock_spec.return_value = None
                engines = get_available_engines()
                assert len(engines) == 1
                assert engines[0].name == "piper"

                # Neither available
                mock_which.side_effect = lambda cmd: None
                engines = get_available_engines()
                assert len(engines) == 0