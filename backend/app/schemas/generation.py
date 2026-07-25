"""
Pydantic v2 schemas for Content Generations (summaries, study guides, etc.)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.constants import GenerationType, TaskStatus

# ─── Request schemas ─────────────────────────────────────────────────────────


class GenerationRequest(BaseModel):
    """Request body for content generation tasks."""

    model: str | None = None  # override default LLM
    max_tokens: int | None = None


# ─── Response schemas ─────────────────────────────────────────────────────────


class GenerationResponse(BaseModel):
    """Single generation record."""

    id: str
    notebook_id: str
    type: GenerationType
    status: TaskStatus | None = None
    content: Any | None
    audio_path: str | None
    task_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
