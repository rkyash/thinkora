"""
FastAPI dependencies — shared across all routers.
get_db: yields async DB session
get_current_user: extracts and validates JWT from Authorization header
get_notebook_or_404: validates notebook exists and user has access
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, NotFoundError, PermissionDeniedError
from app.database import get_async_session
from app.models.notebook import Notebook
from app.models.user import User
from app.models.workspace import Workspace
from app.repositories import notebook_repo, user_repo, workspace_repo
from app.services.auth import decode_token, is_token_blacklisted

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session."""
    async for session in get_async_session():
        yield session


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Extract JWT from Authorization header and return the authenticated user.
    Raises AuthenticationError if token is invalid, expired, or blacklisted.
    """
    from app.config import settings
    if not settings.AUTH_ENABLED:
        user = await user_repo.get_by_email(db, "local@thinkora.app")
        if not user:
            raise AuthenticationError("Local user not initialized")
        return user

    if credentials is None:
        raise AuthenticationError("Not authenticated")

    token = credentials.credentials

    # Check blacklist
    if await is_token_blacklisted(token):
        raise AuthenticationError("Token has been revoked")

    # Decode and validate
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type — use access token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token: missing subject")

    # Fetch user from DB
    user = await user_repo.get(db, user_id)
    if user is None:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("Account is disabled")

    return user


async def get_notebook_or_404(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Notebook:
    """
    Validate that a notebook exists and the current user owns the parent workspace.
    """
    notebook = await notebook_repo.get(db, notebook_id)
    if notebook is None:
        raise NotFoundError("Notebook", notebook_id)

    # Verify ownership through workspace
    workspace = await workspace_repo.get(db, notebook.workspace_id)
    if workspace is None or workspace.owner_id != current_user.id:
        raise PermissionDeniedError("You don't have access to this notebook")

    return notebook


async def get_current_user_for_sse(
    db: AsyncSession = Depends(get_db),
    token: Optional[str] = Query(default=None),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> User:
    """
    Auth dependency for SSE endpoints.
    Browser EventSource cannot set headers, so the JWT is accepted via:
      1. ?token=<jwt>  query param  (EventSource / SSE)
      2. Authorization: Bearer <jwt>  header  (regular HTTP clients)
    """
    from app.config import settings
    if not settings.AUTH_ENABLED:
        user = await user_repo.get_by_email(db, "local@thinkora.app")
        if not user:
            raise AuthenticationError("Local user not initialized")
        return user

    raw_token: Optional[str] = None

    if token:
        raw_token = token
    elif credentials:
        raw_token = credentials.credentials

    if not raw_token:
        raise AuthenticationError("Authentication required")

    if await is_token_blacklisted(raw_token):
        raise AuthenticationError("Token has been revoked")

    payload = decode_token(raw_token)
    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type — use access token")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token: missing subject")

    user = await user_repo.get(db, user_id)
    if user is None:
        raise AuthenticationError("User not found")
    if not user.is_active:
        raise AuthenticationError("Account is disabled")

    return user
