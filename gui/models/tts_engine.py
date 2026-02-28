# ABOUTME: TTS engine abstraction layer for supporting multiple text-to-speech backends.
# ABOUTME: Provides unified interface for Piper, WhisperSpeech, and future engines.

"""TTS engine abstraction and implementations."""

from __future__ import annotations

import importlib.util
import logging
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from gui.models.voice import Voice
from gui.utils.paths import VOICES_DIR

logger = logging.getLogger(__name__)


class EngineNotAvailableError(Exception):
    """Raised when a TTS engine is not available on the system."""

    pass


class TTSEngine(ABC):
    """Abstract base class for text-to-speech engines.

    Each engine implementation must provide methods for:
    - Checking availability
    - Synthesizing text to audio
    - Listing available voices
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the engine name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available on the system.

        Returns:
            True if the engine can be used, False otherwise
        """
        pass

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: Voice,
        output_path: Path,
        **kwargs,
    ) -> None:
        """Synthesize text to audio file.

        Args:
            text: The text to synthesize
            voice: The voice to use
            output_path: Where to save the audio file
            **kwargs: Engine-specific parameters

        Raises:
            EngineNotAvailableError: If the engine is not available
            RuntimeError: If synthesis fails
        """
        pass

    @abstractmethod
    def get_voices(self) -> list[Voice]:
        """Return list of available voices for this engine.

        Returns:
            List of Voice objects with engine field set
        """
        pass


class PiperEngine(TTSEngine):
    """Piper TTS engine implementation."""

    @property
    def name(self) -> str:
        """Return the engine name."""
        return "piper"

    def is_available(self) -> bool:
        """Check if Piper is installed."""
        return shutil.which("piper") is not None

    def synthesize(
        self,
        text: str,
        voice: Voice,
        output_path: Path,
        **kwargs,
    ) -> None:
        """Synthesize text using Piper.

        Args:
            text: The text to synthesize
            voice: The Piper voice to use
            output_path: Where to save the audio file
            **kwargs: Optional parameters like length_scale

        Raises:
            EngineNotAvailableError: If Piper is not installed
            RuntimeError: If synthesis fails
        """
        if not self.is_available():
            raise EngineNotAvailableError("Piper is not installed")

        # Get Piper executable path
        piper_path = shutil.which("piper")
        if not piper_path:
            raise EngineNotAvailableError("Piper executable not found")

        # Build voice model path
        model_path = VOICES_DIR / voice.language / voice.key / f"{voice.key}.onnx"

        if not model_path.exists():
            raise RuntimeError(f"Voice model not found: {model_path}")

        # Build command
        cmd = [
            piper_path,
            "--model",
            str(model_path),
            "--output-file",
            str(output_path),
        ]

        # Add optional parameters
        if "length_scale" in kwargs:
            cmd.extend(["--length_scale", str(kwargs["length_scale"])])

        logger.info("Running Piper synthesis: %s", " ".join(cmd))

        # Run Piper
        try:
            result = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                check=True,
            )
            logger.debug("Piper output: %s", result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error("Piper synthesis failed: %s", e.stderr)
            raise RuntimeError(f"Piper synthesis failed: {e.stderr}") from e

    def get_voices(self) -> list[Voice]:
        """Return list of installed Piper voices.

        Scans the Piper voices directory for installed models.
        """
        voices = []

        if not VOICES_DIR.exists():
            return voices

        # Find all .onnx files
        for onnx_path in VOICES_DIR.glob("*/*/*.onnx"):
            # Extract voice information from path
            # Format: voices_dir/language/voice_key/voice_key.onnx
            voice_key = onnx_path.stem
            language = onnx_path.parent.parent.name

            # Parse voice key for name and quality
            # Format: language-name-quality
            parts = voice_key.split("-")
            if len(parts) >= 3:
                # Extract quality (last part)
                quality = parts[-1]
                # Extract name (middle parts, excluding language prefix)
                name_parts = parts[1:-1] if len(parts) > 3 else [parts[1]]
                name = "_".join(name_parts).title()
            else:
                quality = "medium"
                name = voice_key

            # Check for config file
            config_path = onnx_path.with_suffix(".onnx.json")
            files = {
                ".onnx": {"size_bytes": onnx_path.stat().st_size},
            }
            if config_path.exists():
                files[".onnx.json"] = {"size_bytes": config_path.stat().st_size}

            voice = Voice(
                key=voice_key,
                name=name,
                language=language,
                quality=quality,
                engine="piper",
                files=files,
                size_bytes=sum(f["size_bytes"] for f in files.values()),
                installed=True,
            )
            voices.append(voice)

        return sorted(voices, key=lambda v: (v.language, v.name, v.quality))


class WhisperSpeechEngine(TTSEngine):
    """WhisperSpeech TTS engine implementation."""

    def __init__(self):
        """Initialize WhisperSpeech engine."""
        self._pipeline = None

    @property
    def name(self) -> str:
        """Return the engine name."""
        return "whisperspeech"

    def is_available(self) -> bool:
        """Check if WhisperSpeech is installed."""
        return importlib.util.find_spec("whisperspeech") is not None

    def synthesize(
        self,
        text: str,
        voice: Voice,
        output_path: Path,
        **kwargs,
    ) -> None:
        """Synthesize text using WhisperSpeech.

        Args:
            text: The text to synthesize
            voice: The WhisperSpeech voice to use
            output_path: Where to save the audio file
            **kwargs: Optional parameters for WhisperSpeech

        Raises:
            EngineNotAvailableError: If WhisperSpeech is not installed
            RuntimeError: If synthesis fails
        """
        if not self.is_available():
            raise EngineNotAvailableError("WhisperSpeech is not installed")

        # Lazy load WhisperSpeech to avoid import errors when not installed
        try:
            # Import modules dynamically
            import importlib
            torch = importlib.import_module("torch")
            whisperspeech_pipeline = importlib.import_module("whisperspeech.pipeline")
            Pipeline = whisperspeech_pipeline.Pipeline
            soundfile = importlib.import_module("soundfile")

            # Initialize pipeline if needed
            if self._pipeline is None:
                logger.info("Initializing WhisperSpeech pipeline...")
                # Use CPU by default, GPU if available
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._pipeline = Pipeline(device=device)
                logger.info("WhisperSpeech pipeline initialized on %s", device)

            logger.info("Synthesizing text with WhisperSpeech...")

            # Generate audio
            audio = self._pipeline.generate(text)

            # Save to file
            # WhisperSpeech returns audio as numpy array or tensor
            # Ensure audio is numpy array
            if hasattr(audio, "cpu"):
                audio = audio.cpu().numpy()

            # Save audio (assuming 24kHz sample rate - WhisperSpeech default)
            soundfile.write(str(output_path), audio, 24000)

            logger.info("WhisperSpeech synthesis complete: %s", output_path)

        except ImportError as e:
            raise EngineNotAvailableError(
                f"WhisperSpeech dependencies not available: {e}"
            ) from e
        except Exception as e:
            logger.error("WhisperSpeech synthesis failed: %s", e)
            raise RuntimeError(f"WhisperSpeech synthesis failed: {e}") from e

    def get_voices(self) -> list[Voice]:
        """Return list of available WhisperSpeech voices.

        WhisperSpeech currently uses a single default voice model.
        Voice cloning support may be added in the future.
        """
        # WhisperSpeech doesn't have multiple pre-trained voices like Piper
        # It uses a single model that can be customized with voice cloning
        return [
            Voice(
                key="whisperspeech-default",
                name="Default",
                language="en",
                quality="high",
                engine="whisperspeech",
                files={},
                size_bytes=0,
                installed=self.is_available(),
            )
        ]


# Engine registry
_engines = {
    "piper": PiperEngine,
    "whisperspeech": WhisperSpeechEngine,
}


def get_engine(name: str) -> TTSEngine:
    """Get a TTS engine by name.

    Args:
        name: The engine name ("piper" or "whisperspeech")

    Returns:
        An instance of the requested engine

    Raises:
        ValueError: If the engine name is unknown
    """
    if name not in _engines:
        raise ValueError(f"Unknown engine: {name}")

    engine_class = _engines[name]
    return engine_class()


def get_available_engines() -> list[TTSEngine]:
    """Get list of available TTS engines.

    Returns:
        List of engine instances that are available on the system
    """
    available = []
    for name in _engines:
        engine = get_engine(name)
        if engine.is_available():
            available.append(engine)
    return available


def register_engine(name: str, engine_class: type[TTSEngine]) -> None:
    """Register a new TTS engine.

    Args:
        name: The engine name
        engine_class: The engine class (must inherit from TTSEngine)
    """
    if not issubclass(engine_class, TTSEngine):
        raise TypeError(f"{engine_class} must inherit from TTSEngine")
    _engines[name] = engine_class