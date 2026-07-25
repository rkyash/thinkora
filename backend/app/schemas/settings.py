"""
Settings Schemas — request/response models for /api/v1/settings.

Design decisions:
  - API keys are NEVER returned in plaintext. GET responses always mask them.
  - Settings are stored as string key-value pairs in app_settings table.
  - TASK-199: env-only strategy — keys are read from DB but can fall back to env.
  - TASK-200: Keys masked to "••••••••" in GET responses.
"""

from __future__ import annotations

from enum import Enum


from pydantic import BaseModel, Field


# ─── Configurable Setting Keys ────────────────────────────────────────────────

class SettingKey(str, Enum):
    """All valid setting keys that can be read or written via the API."""

    # LLM provider API keys
    ACTIVE_PROVIDER = "active_provider"
    OPENAI_API_KEY = "openai_api_key"
    ANTHROPIC_API_KEY = "anthropic_api_key"
    GEMINI_API_KEY = "gemini_api_key"
    GROQ_API_KEY = "groq_api_key"
    MISTRAL_API_KEY = "mistral_api_key"
    OPENROUTER_API_KEY = "openrouter_api_key"
    OPENAI_PROXY_BASE_URL = "openai_proxy_base_url"
    OPENAI_PROXY_API_KEY = "openai_proxy_api_key"
    OPENAI_PROXY_MODEL = "openai_proxy_model"
    OLLAMA_BASE_URL = "ollama_base_url"

    # Global model defaults
    DEFAULT_CHAT_MODEL = "default_chat_model"
    DEFAULT_GENERATION_MODEL = "default_generation_model"

    # Per-provider selected model (LiteLLM model string, without provider prefix)
    OPENAI_MODEL = "openai_model"
    ANTHROPIC_MODEL = "anthropic_model"
    GEMINI_MODEL = "gemini_model"
    GROQ_MODEL = "groq_model"
    MISTRAL_MODEL = "mistral_model"
    OPENROUTER_MODEL = "openrouter_model"
    OLLAMA_MODEL = "ollama_model"

    # Appearance preferences (stored per-user, no backend effect)
    THEME = "theme"
    FONT_SIZE = "font_size"
    COMPACT_MODE = "compact_mode"


# Keys that contain secrets — masked in GET responses
_SECRET_KEYS: frozenset[str] = frozenset({
    SettingKey.OPENAI_API_KEY,
    SettingKey.ANTHROPIC_API_KEY,
    SettingKey.GEMINI_API_KEY,
    SettingKey.GROQ_API_KEY,
    SettingKey.MISTRAL_API_KEY,
    SettingKey.OPENROUTER_API_KEY,
    SettingKey.OPENAI_PROXY_API_KEY,
})

MASK = "••••••••"


def is_secret(key: str) -> bool:
    """Return True if this key holds a secret (API key) that must be masked."""
    return key in _SECRET_KEYS


def mask_value(key: str, value: str | None) -> str | None:
    """Mask the value if the key is a secret and the value is set."""
    if value and is_secret(key):
        return MASK
    return value


# ─── Provider metadata ────────────────────────────────────────────────────────

class ProviderInfo(BaseModel):
    """Static metadata about an LLM provider."""
    id: str
    name: str
    description: str
    key_setting: str | None          # which SettingKey holds its API key
    model_setting: str | None        # which SettingKey holds the selected model for this provider
    base_url_setting: str | None = None
    selected_base_url: str | None = None
    supports_fetch_models: bool = False
    requires_key: bool               # False for Ollama (local)
    is_configured: bool              # True when key is set (non-empty)
    selected_model: str | None = None  # current value of model_setting (plaintext — not a secret)


# ─── Response Schemas ─────────────────────────────────────────────────────────

class SettingResponse(BaseModel):
    """Single setting key-value pair (value masked if secret)."""
    key: str
    value: str | None
    is_secret: bool


class SettingsResponse(BaseModel):
    """Full settings payload returned by GET /settings."""
    settings: list[SettingResponse]
    providers: list[ProviderInfo]


# ─── Request Schemas ──────────────────────────────────────────────────────────

class SettingUpdate(BaseModel):
    """Payload for PUT /settings/{key}."""
    value: str = Field(..., description="New value for the setting. Pass empty string to clear.")


class BulkSettingsUpdate(BaseModel):
    """Payload for PUT /settings — update multiple keys at once."""
    settings: dict[str, str] = Field(
        ...,
        description="Map of setting key → new value. Unknown keys are ignored.",
        examples=[{"openai_api_key": "sk-...", "default_chat_model": "gpt-4o"}],
    )


# ─── Provider Test ────────────────────────────────────────────────────────────

class ProviderTestResponse(BaseModel):
    """Result of POST /settings/test/{provider_id}."""
    provider_id: str
    success: bool
    message: str
    model_count: int | None = None    # number of available models if testable
