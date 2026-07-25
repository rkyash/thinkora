"""
Audio processor — transcribes audio files to text using Whisper.

Supports common audio formats: MP3, WAV, M4A, FLAC, OGG, etc.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.core.logging import logger
from app.services.parsers import BaseParser

# Model size - tiny is fastest, good for English
# Other options: tiny, base, small, medium, large-v1, large-v2, large-v3
_MODEL_SIZE = "tiny"
_MODEL_PATH_OR_REPO = _MODEL_SIZE

# Global model instance to avoid reloading
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    """Get or create the Whisper model instance."""
    global _model
    if _model is None:
        logger.info("audio_model_loading", model=_MODEL_SIZE)
        _model = WhisperModel(
            _MODEL_PATH_OR_REPO,
            device="cpu",  # Can be changed to "cuda" if GPU available
            compute_type="int8",  # int8 for speed, float16 for accuracy
        )
        logger.info("audio_model_loaded", model=_MODEL_SIZE)
    return _model


class AudioParser(BaseParser):
    """Transcribe audio files to text using Whisper speech recognition."""

    supported_types: set[SourceType] = {SourceType.AUDIO}

    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """Transcribe audio file to text.

        Args:
            data: Raw audio file content as bytes.
            filename: Original filename (used for logging and format hints).

        Returns:
            Transcribed text from the audio.

        Raises:
            ValidationError: If the audio cannot be processed or transcribed.
        """
        logger.info("audio_transcribe_start", filename=filename, size=len(data))

        if not data:
            raise ValidationError("Empty audio file provided.")

        # Write audio data to temporary file for Whisper processing
        # Determine file extension from filename or default to .wav
        suffix = Path(filename).suffix.lower() if filename else ".wav"
        if not suffix:
            suffix = ".wav"

        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
                tmp_file.write(data)
                tmp_file_path = tmp_file.name

            # Transcribe using Whisper
            model = _get_model()
            segments, info = model.transcribe(
                tmp_file_path,
                language="en",  # Default to English; can be made configurable
                beam_size=5,
                best_of=5,
                patience=1.0,
                length_penalty=1.0,
                temperature=0.0,
                compression_ratio_threshold=2.4,
                log_prob_threshold=-1.0,
                no_speech_threshold=0.6,
                condition_on_previous_text=True,
                prompt_reset_on_temperature=0.0,
                # timestamp_rounding=0.01,  # Newer versions
            )

            # Collect all transcribed text
            transcript_parts = []
            for segment in segments:
                transcript_parts.append(segment.text.strip())

            transcript = " ".join(transcript_parts).strip()

            if not transcript:
                logger.warning(
                    "audio_transcribe_empty",
                    filename=filename,
                    duration=info.duration,
                )
                return ""  # Return empty string rather than error for silent audio

            logger.info(
                "audio_transcribe_complete",
                filename=filename,
                duration=info.duration,
                language=info.language,
                probability=round(getattr(info, "language_probability", 0), 2),
                text_length=len(transcript),
            )

            return transcript

        except Exception as exc:
            logger.error(
                "audio_transcribe_failed",
                filename=filename,
                error=str(exc),
                exc_info=True,
            )
            raise ValidationError(
                f"Failed to transcribe audio file '{filename}': {str(exc)}"
            ) from exc

        finally:
            # Clean up temporary file
            try:
                if "tmp_file_path" in locals():
                    Path(tmp_file_path).unlink(missing_ok=True)
            except Exception:
                pass  # Ignore cleanup errors
