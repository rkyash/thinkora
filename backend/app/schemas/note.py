"""
Pydantic v2 schemas for Notes — request bodies and response shapes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BacklinkItem(BaseModel):
    """A backlink reference stored in a note."""

    note_id: str
    title: str


# ─── Request schemas ─────────────────────────────────────────────────────────


class NoteCreate(BaseModel):
    """Create a new note."""

    title: str | None = None
    content: str | None = None  # TipTap JSON or plain markdown


class NoteUpdate(BaseModel):
    """Update an existing note — all fields optional."""

    title: str | None = None
    content: str | None = None
    backlinks: list[BacklinkItem] | None = None


class NoteSummarizeRequest(BaseModel):
    """Request body for AI note summarization."""

    model: str | None = None  # override default LLM


# ─── Response schemas ─────────────────────────────────────────────────────────


class NoteResponse(BaseModel):
    """Single note response."""

    id: str
    notebook_id: str
    title: str | None
    content: str | None
    backlinks: Any | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NoteSummaryResponse(BaseModel):
    """Response for AI note summarization."""

    note_id: str
    summary: str
