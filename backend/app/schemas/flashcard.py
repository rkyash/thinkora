"""
Pydantic v2 schemas for Flashcards — request bodies and response shapes.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.core.constants import Difficulty

# ─── Request schemas ─────────────────────────────────────────────────────────


class FlashcardGenerateRequest(BaseModel):
    """Request body for AI flashcard generation."""

    count: int = 10  # how many cards to generate
    difficulty: Difficulty | None = None  # filter by difficulty
    topic: str | None = None  # optional topic focus
    model: str | None = None  # override default LLM


class FlashcardCreate(BaseModel):
    """Manually create a flashcard."""

    question: str
    answer: str
    difficulty: Difficulty = Difficulty.MEDIUM


# ─── Response schemas ─────────────────────────────────────────────────────────


class FlashcardResponse(BaseModel):
    """Single flashcard response."""

    id: str
    notebook_id: str
    question: str
    answer: str
    difficulty: Difficulty
    created_at: datetime

    model_config = {"from_attributes": True}


class FlashcardGenerateResponse(BaseModel):
    """Response after dispatching flashcard generation task."""

    task_id: str
    message: str = "Flashcard generation started"
