"""
Pydantic v2 schemas for Podcast Audio generation.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.generation import GenerationResponse


class AudioGenerateRequest(BaseModel):
    """Request body for podcast generation."""
    tts_backend: str = "gtts"
    model: Optional[str] = None


class AudioStatusResponse(BaseModel):
    """Response when polling for audio generation status."""
    generation: GenerationResponse
    audio_url: Optional[str] = None
