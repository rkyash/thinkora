"""
Notebook schemas — request/response models.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NotebookCreate(BaseModel):
    """Create notebook request."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    emoji: str = Field(default="📓", max_length=10)


class NotebookUpdate(BaseModel):
    """Update notebook request."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    emoji: str | None = Field(default=None, max_length=10)


class NotebookResponse(BaseModel):
    """Notebook response."""

    id: str
    workspace_id: str
    name: str
    description: str | None = None
    emoji: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
