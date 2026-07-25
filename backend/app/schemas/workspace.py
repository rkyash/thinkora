"""
Workspace schemas — request/response models.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    """Create workspace request."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class WorkspaceUpdate(BaseModel):
    """Update workspace request."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class WorkspaceResponse(BaseModel):
    """Workspace response."""

    id: str
    owner_id: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
