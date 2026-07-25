"""
Auth API — registration, login, token refresh, logout, profile.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.response import ApiResponse
from app.schemas.user import UpdatePasswordRequest, UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.auth import blacklist_token, login_user, refresh_tokens, register_user, update_password_by_email


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=ApiResponse)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user account and return JWT tokens."""
    user_dict, tokens = await register_user(db, data)
    return {
        "success": True,
        "data": {
            "user": user_dict,
            "tokens": tokens.model_dump(),
        },
        "message": "Registration successful",
    }


@router.post("/login", response_model=ApiResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    user_dict, tokens = await login_user(db, data.email, data.password)
    return {
        "success": True,
        "data": {
            "user": user_dict,
            "tokens": tokens.model_dump(),
        },
        "message": "Login successful",
    }


@router.post("/refresh", response_model=ApiResponse)
async def refresh(authorization: str = Header(default="")):
    """Refresh access token using a valid refresh token."""
    if not authorization.startswith("Bearer "):
        from app.core.exceptions import AuthenticationError
        raise AuthenticationError("Missing refresh token")

    refresh_token = authorization.removeprefix("Bearer ").strip()
    tokens = await refresh_tokens(refresh_token)
    return {
        "success": True,
        "data": tokens.model_dump(),
        "message": "Tokens refreshed",
    }


@router.post("/logout", response_model=ApiResponse)
async def logout(authorization: str = Header(default="")):
    """Blacklist current token (logout)."""
    if authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        await blacklist_token(token)
    return {
        "success": True,
        "data": None,
        "message": "Logged out successfully",
    }


@router.get("/me", response_model=ApiResponse[UserResponse])
async def me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return {
        "success": True,
        "data": UserResponse.model_validate(current_user),
    }

@router.post("/update-password", response_model=ApiResponse)
async def update_password(
    data: UpdatePasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update the user's password."""
    new_password = data.new_password
    email = data.email

    await update_password_by_email(db, email, new_password)
    return {
        "success": True,
        "data": None,
        "message": "Password updated successfully",
    }