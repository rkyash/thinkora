"""
Settings API — /api/v1/settings

Endpoints:
  GET    /settings                  Return all settings (secrets masked)
  PUT    /settings                  Bulk-update multiple settings
  PUT    /settings/{key}            Update a single setting
  DELETE /settings/{key}            Clear/reset a setting
  POST   /settings/test/{provider}  Test provider connectivity
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.response import ApiResponse, ok
from app.schemas.settings import (
    BulkSettingsUpdate,
    ProviderTestResponse,
    SettingResponse,
    SettingsResponse,
    SettingUpdate,
)
from app.services.settings import SettingsService

router = APIRouter(tags=["Settings"])


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _svc(db: AsyncSession) -> SettingsService:
    return SettingsService(db)


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get(
    "/settings",
    response_model=ApiResponse[SettingsResponse],
)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ApiResponse[SettingsResponse]:
    """
    Return all configurable settings with API keys masked.
    Includes provider status (is_configured) for each LLM provider.
    """
    data = await _svc(db).get_all()
    return ok(data)


@router.put(
    "/settings",
    response_model=ApiResponse[list[SettingResponse]],
)
async def bulk_update_settings(
    payload: BulkSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ApiResponse[list[SettingResponse]]:
    """
    Update multiple settings at once.
    Unknown keys are silently ignored.
    API key values are masked in the response.
    """
    results = await _svc(db).bulk_upsert(payload.settings)
    return ok(results, f"Updated {len(results)} setting(s)")


@router.put(
    "/settings/{key}",
    response_model=ApiResponse[SettingResponse],
)
async def update_setting(
    key: str,
    payload: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ApiResponse[SettingResponse]:
    """
    Update a single setting by key.
    Pass an empty string to clear the value.
    """
    try:
        result = await _svc(db).upsert(key, payload.value)
    except ValueError as exc:
        raise AppError(str(exc), status_code=400, code="INVALID_SETTING_KEY") from exc
    return ok(result, f"Setting '{key}' updated")


@router.delete(
    "/settings/{key}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
async def clear_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ApiResponse[None]:
    """Clear/reset a setting to its environment variable default."""
    from app.repositories.app_settings import app_settings_repo

    deleted = await app_settings_repo.delete(db, key)
    msg = f"Setting '{key}' cleared" if deleted else f"Setting '{key}' was not set"
    return ok(None, msg)


@router.post(
    "/settings/test/{provider_id}",
    response_model=ApiResponse[ProviderTestResponse],
)
async def test_provider(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ApiResponse[ProviderTestResponse]:
    """
    Test connectivity to a specific LLM provider.
    Sends a minimal chat request with max_tokens=5 to verify the API key works.
    """
    result = await _svc(db).test_provider(provider_id)
    return ok(
        ProviderTestResponse(**result),
        "Test complete",
    )


@router.get(
    "/settings/models/{provider_id}",
    response_model=ApiResponse[list[str]],
)
async def fetch_models(
    provider_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ApiResponse[list[str]]:
    """
    Fetch available models dynamically from the provider API.
    Used for local models (Ollama) or custom OpenAI-compatible proxies.
    """
    models = await _svc(db).fetch_provider_models(provider_id)
    return ok(models, f"Fetched {len(models)} models")
