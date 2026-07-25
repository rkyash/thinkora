"""
Authentication service — JWT creation/validation, password hashing, token blacklist.
"""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.cache import get_redis
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.logging import logger
from app.repositories import user_repo, workspace_repo
from app.schemas.user import TokenResponse, UserCreate

# JWT config
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE = timedelta(days=7)
TOKEN_BLACKLIST_PREFIX = "blacklist:"


# ─── Password Hashing ────────────────────────────────────────────


def _pre_hash(password: str) -> bytes:
    """Pre-hash password with SHA-256 to work around bcrypt's 72-byte limit.

    bcrypt truncates passwords longer than 72 bytes.  By running the
    password through SHA-256 first and base64-encoding the digest we get
    a fixed 44-byte ASCII string that is always under the limit, while
    preserving full entropy of the original password.

    This is the same approach used by Dropbox, Django, and other major
    frameworks.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(_pre_hash(password), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(_pre_hash(plain), hashed.encode("ascii"))


def create_access_token(user_id: str) -> str:
    """Create a short-lived access JWT."""
    expire = datetime.now(UTC) + ACCESS_TOKEN_EXPIRE
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived refresh JWT."""
    expire = datetime.now(UTC) + REFRESH_TOKEN_EXPIRE
    payload = {"sub": user_id, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises AuthenticationError on failure."""
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token: missing subject")
        return payload
    except PyJWTError as e:
        raise AuthenticationError(f"Invalid or expired token: {e}") from e


async def is_token_blacklisted(token: str) -> bool:
    """Check if a token has been blacklisted (logout)."""
    redis = await get_redis()
    return bool(await redis.exists(f"{TOKEN_BLACKLIST_PREFIX}{token}") > 0)


async def blacklist_token(token: str) -> None:
    """Add a token to the blacklist with its remaining TTL."""
    try:
        payload = decode_token(token)
        exp = payload.get("exp", 0)
        now = datetime.now(UTC).timestamp()
        ttl = max(int(exp - now), 1)
        redis = await get_redis()
        await redis.setex(f"{TOKEN_BLACKLIST_PREFIX}{token}", ttl, "1")
    except AuthenticationError:
        pass  # Already expired, no need to blacklist


async def register_user(db: AsyncSession, data: UserCreate) -> tuple[dict[str, Any], TokenResponse]:
    """Register a new user. Returns (user_dict, tokens)."""
    # Check for existing email/username
    existing = await user_repo.get_by_email(db, data.email)
    if existing:
        raise ConflictError("Email already registered")

    existing = await user_repo.get_by_username(db, data.username)
    if existing:
        raise ConflictError("Username already taken")

    # Create user
    user = await user_repo.create(
        db,
        {
            "email": data.email,
            "username": data.username,
            "hashed_password": hash_password(data.password),
        },
    )

    # Create default workspace
    await workspace_repo.create(
        db,
        {
            "owner_id": user.id,
            "name": "My Workspace",
            "description": "Default workspace for notes and notebooks.",
        },
    )

    logger.info("user_registered", user_id=user.id, email=user.email)

    # Generate tokens
    tokens = TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }, tokens


async def login_user(db: AsyncSession, email: str, password: str) -> tuple[dict[str, Any], TokenResponse]:
    """Authenticate user and return tokens."""
    user = await user_repo.get_by_email_or_username(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise AuthenticationError("Invalid email/username or password")

    if not user.is_active:
        raise AuthenticationError("Account is disabled")

    logger.info("user_logged_in", user_id=user.id)

    tokens = TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }, tokens


async def refresh_tokens(refresh_token: str) -> TokenResponse:
    """Validate refresh token and issue new token pair."""
    if await is_token_blacklisted(refresh_token):
        raise AuthenticationError("Token has been revoked")

    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise AuthenticationError("Invalid token type")

    user_id = payload["sub"]

    # Blacklist the old refresh token
    await blacklist_token(refresh_token)

    return TokenResponse(
        access_token=create_access_token(user_id),
        refresh_token=create_refresh_token(user_id),
    )


async def update_password_by_email(db: AsyncSession, email: str, new_password: str) -> None:
    """Update the user's password."""
    user = await user_repo.get_by_email_or_username(db, email)
    if not user:
        raise AuthenticationError("User not found")

    hashed_password = hash_password(new_password)
    await user_repo.update(db, user.id, {"hashed_password": hashed_password})
    logger.info("user_password_updated", user_id=user.id)
