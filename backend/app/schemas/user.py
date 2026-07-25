"""
User schemas — request/response models for authentication.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ─── Request Schemas ──────────────────────────────────────────

class UserCreate(BaseModel):
    """Registration request."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Login request."""

    email: str
    password: str


class UpdatePasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(min_length=8, max_length=128)

# ─── Response Schemas ─────────────────────────────────────────

class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token payload."""

    user_id: str
    exp: datetime | None = None
