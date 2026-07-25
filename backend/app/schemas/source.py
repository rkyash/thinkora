"""
Source schemas — request/response models for source management.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator

from app.core.constants import SourceStatus, SourceType

# ─── Request Schemas ──────────────────────────────────────────


class SourceUploadRequest(BaseModel):
    """File upload source request."""

    filename: str = Field(..., max_length=255, description="Original filename")


class SourceUrlRequest(BaseModel):
    """URL source request."""

    name: str = Field(..., max_length=255, description="Name of the source")
    url: HttpUrl = Field(..., description="URL to fetch content from")


class SourceYoutubeRequest(BaseModel):
    """YouTube source request."""

    name: str = Field(..., max_length=255, description="Name of the source")
    url: HttpUrl = Field(..., description="YouTube video URL")


class SourceTextRequest(BaseModel):
    """Text input source request."""

    content: str = Field(
        ...,
        min_length=1,
        max_length=100000,
        description="Text content to process",
    )
    name: str | None = Field(
        None,
        max_length=255,
        description="Name of the source",
    )


# ─── Response Schemas ─────────────────────────────────────────


class SourceResponse(BaseModel):
    """Source response model."""

    id: UUID
    notebook_id: UUID
    name: str | None = None
    type: SourceType
    status: SourceStatus
    file_path: str | None = None
    url: str | None = None
    char_count: int | None = None
    chunk_count: int | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceListResponse(BaseModel):
    """Source list response model."""

    id: UUID
    notebook_id: UUID
    name: str | None = None
    type: SourceType
    status: SourceStatus
    created_at: datetime

    model_config = {"from_attributes": True}
