"""
Settings Service — reads and writes application settings.

Design principles:
  - API keys are NEVER returned in plaintext. All GET operations mask secrets.
  - Settings fall back to environment variables when no DB override exists.
  - Provider test calls are made via LiteLLM to stay provider-agnostic.
  - TASK-199/200: env-only strategy + masking.
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.config import settings as env_settings
from app.repositories.app_settings import app_settings_repo
from app.schemas.settings import (
    _SECRET_KEYS,
    MASK,
    ProviderInfo,
    SettingKey,
    SettingResponse,
    SettingsResponse,
    is_secret,
    mask_value,
)

log = structlog.get_logger(__name__)

# ─── Provider registry ────────────────────────────────────────────────────────

_PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "ollama",
        "name": "Ollama (Local)",
        "description": "Local inference server for Llama 3, Mistral, Phi-3, Qwen, etc.",
        "key_setting": None,
        "model_setting": SettingKey.OLLAMA_MODEL,
        "base_url_setting": SettingKey.OLLAMA_BASE_URL,
        "requires_key": False,
        "supports_fetch_models": True,
    },
    {
        "id": "openai_proxy",
        "name": "Custom OpenAI-Compatible Proxy",
        "description": "NVIDIA NIM, vLLM, LM Studio, etc. custom endpoint.",
        "key_setting": SettingKey.OPENAI_PROXY_API_KEY,
        "model_setting": SettingKey.OPENAI_PROXY_MODEL,
        "base_url_setting": SettingKey.OPENAI_PROXY_BASE_URL,
        "requires_key": False,
        "supports_fetch_models": True,
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "description": "Cloud access for GPT-4o, GPT-4o-mini, and GPT-3.5 Turbo.",
        "key_setting": SettingKey.OPENAI_API_KEY,
        "model_setting": SettingKey.OPENAI_MODEL,
        "requires_key": True,
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude",
        "description": "Claude 3.5 Sonnet and Haiku — best-in-class reasoning.",
        "key_setting": SettingKey.ANTHROPIC_API_KEY,
        "model_setting": SettingKey.ANTHROPIC_MODEL,
        "requires_key": True,
    },
    {
        "id": "gemini",
        "name": "Google Gemini",
        "description": "Gemini 1.5 Flash / Pro — fast multimodal models.",
        "key_setting": SettingKey.GEMINI_API_KEY,
        "model_setting": SettingKey.GEMINI_MODEL,
        "requires_key": True,
    },
    {
        "id": "groq",
        "name": "Groq Cloud",
        "description": "Ultra-fast inference for Llama 3, Mixtral, Gemma.",
        "key_setting": SettingKey.GROQ_API_KEY,
        "model_setting": SettingKey.GROQ_MODEL,
        "requires_key": True,
    },
    {
        "id": "mistral",
        "name": "Mistral AI",
        "description": "Mistral Large, Mistral 7B — French-built frontier models.",
        "key_setting": SettingKey.MISTRAL_API_KEY,
        "model_setting": SettingKey.MISTRAL_MODEL,
        "requires_key": True,
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "description": "Unified API gateway for 100+ models from every major provider.",
        "key_setting": SettingKey.OPENROUTER_API_KEY,
        "model_setting": SettingKey.OPENROUTER_MODEL,
        "requires_key": True,
    },
]

# Map env fallbacks: setting key → Settings attribute name
_ENV_FALLBACKS: dict[str, str] = {
    SettingKey.ACTIVE_PROVIDER: "ACTIVE_PROVIDER",
    SettingKey.OPENAI_API_KEY: "OPENAI_API_KEY",
    SettingKey.ANTHROPIC_API_KEY: "ANTHROPIC_API_KEY",
    SettingKey.GEMINI_API_KEY: "GEMINI_API_KEY",
    SettingKey.GROQ_API_KEY: "GROQ_API_KEY",
    SettingKey.MISTRAL_API_KEY: "MISTRAL_API_KEY",
    SettingKey.OPENROUTER_API_KEY: "OPENROUTER_API_KEY",
    SettingKey.OPENAI_PROXY_BASE_URL: "OPENAI_PROXY_BASE_URL",
    SettingKey.OPENAI_PROXY_API_KEY: "OPENAI_PROXY_API_KEY",
    SettingKey.OLLAMA_BASE_URL: "OLLAMA_BASE_URL",
    SettingKey.DEFAULT_CHAT_MODEL: "DEFAULT_MODEL",
    SettingKey.OPENAI_MODEL: "OPENAI_MODEL",
    SettingKey.ANTHROPIC_MODEL: "ANTHROPIC_MODEL",
    SettingKey.GEMINI_MODEL: "GEMINI_MODEL",
    SettingKey.GROQ_MODEL: "GROQ_MODEL",
    SettingKey.MISTRAL_MODEL: "MISTRAL_MODEL",
    SettingKey.OPENROUTER_MODEL: "OPENROUTER_MODEL",
    SettingKey.OLLAMA_MODEL: "OLLAMA_MODEL",
    SettingKey.OPENAI_PROXY_MODEL: "OPENAI_PROXY_MODEL",
}


class SettingsService:
    """
    Manages application settings with DB persistence and env fallback.
    API keys are masked in all read responses.
    """

    def __init__(self, db: Any) -> None:
        self._db = db

    # ─── Read ─────────────────────────────────────────────────────────────────

    async def get_all(self) -> SettingsResponse:
        """
        Return all configurable settings with secrets masked.
        Values are resolved: DB override takes precedence over env variable.
        """
        all_keys = list(SettingKey)
        db_values = await app_settings_repo.get_many(self._db, [k.value for k in all_keys])

        setting_items: list[SettingResponse] = []
        for key in all_keys:
            raw_value = db_values.get(key.value)

            # Fall back to env if no DB override
            if not raw_value and key.value in _ENV_FALLBACKS:
                raw_value = getattr(env_settings, _ENV_FALLBACKS[key.value], None) or None

            masked = mask_value(key.value, raw_value)
            setting_items.append(
                SettingResponse(
                    key=key.value,
                    value=masked,
                    is_secret=is_secret(key.value),
                )
            )

        # Build provider infos with is_configured derived from key presence
        providers = await self._build_provider_infos(db_values)

        return SettingsResponse(settings=setting_items, providers=providers)

    async def get_value(self, key: str) -> str | None:
        """
        Read a single setting value (plaintext — for internal use only).
        Falls back to env variable when no DB record exists.
        """
        value = await app_settings_repo.get_value(self._db, key)
        if not value and key in _ENV_FALLBACKS:
            value = getattr(env_settings, _ENV_FALLBACKS[key], None) or None
        return value

    # ─── Write ────────────────────────────────────────────────────────────────

    async def upsert(self, key: str, value: str) -> SettingResponse:
        """
        Save a setting to the DB. Returns the response with secret masked.
        Raises ValueError for unknown keys.
        """
        valid_keys = {k.value for k in SettingKey}
        if key not in valid_keys:
            raise ValueError(f"Unknown setting key: {key!r}")

        await app_settings_repo.upsert(self._db, key, value)
        log.info("setting_updated", key=key, is_secret=is_secret(key))

        # If this is an LLM API key, refresh the LLM service env var at runtime
        if key in _ENV_FALLBACKS:
            env_attr = _ENV_FALLBACKS[key]
            if hasattr(env_settings, env_attr) and value and value.strip():
                object.__setattr__(env_settings, env_attr, value)

        masked = mask_value(key, value)
        return SettingResponse(key=key, value=masked, is_secret=is_secret(key))

    async def bulk_upsert(self, updates: dict[str, str]) -> list[SettingResponse]:
        """Update multiple settings at once. Unknown keys are silently skipped."""
        valid_keys = {k.value for k in SettingKey}
        results: list[SettingResponse] = []
        for key, value in updates.items():
            if key not in valid_keys:
                log.warning("settings_bulk_unknown_key", key=key)
                continue
            result = await self.upsert(key, value)
            results.append(result)
        return results

    # ─── Provider test ────────────────────────────────────────────────────────

    async def test_provider(self, provider_id: str) -> dict[str, Any]:
        """
        Test connectivity to an LLM provider by sending a minimal chat request.
        Returns dict with success, message, and model_count.
        """
        provider = next((p for p in _PROVIDERS if p["id"] == provider_id), None)
        if not provider:
            return {
                "provider_id": provider_id,
                "success": False,
                "message": "Unknown provider",
                "model_count": None,
            }

        # Get the key value (plaintext — internal use only)
        key_setting = provider.get("key_setting")
        api_key: str | None = None
        if key_setting:
            api_key = await self.get_value(key_setting)
            if not api_key:
                return {
                    "provider_id": provider_id,
                    "success": False,
                    "message": f"No API key configured for {provider['name']}.",
                    "model_count": None,
                }

        # For ollama and openai_proxy, testing by fetching models is safer than guessing a model string
        if provider.get("supports_fetch_models"):
            try:
                models = await self.fetch_provider_models(provider_id)
                return {
                    "provider_id": provider_id,
                    "success": True,
                    "message": f"Connected successfully. Found {len(models)} models.",
                    "model_count": len(models),
                }
            except Exception as exc:
                log.warning("provider_test_failed", provider=provider_id, error=str(exc))
                return {
                    "provider_id": provider_id,
                    "success": False,
                    "message": f"Connection failed: {str(exc)[:200]}",
                    "model_count": None,
                }

        try:
            result = await asyncio.to_thread(_probe_provider, provider_id, api_key)
            return {"provider_id": provider_id, **result}
        except Exception as exc:
            log.warning("provider_test_failed", provider=provider_id, error=str(exc))
            return {
                "provider_id": provider_id,
                "success": False,
                "message": f"Connection failed: {str(exc)[:200]}",
                "model_count": None,
            }

    async def fetch_provider_models(self, provider_id: str) -> list[str]:
        """Fetch available models from the provider's API."""
        import httpx

        provider = next((p for p in _PROVIDERS if p["id"] == provider_id), None)
        if not provider:
            raise ValueError("Unknown provider")

        base_url_setting = provider.get("base_url_setting")
        if not base_url_setting:
            raise ValueError(
                "Provider does not support fetching models or base URL is not configured"
            )

        base_url = await self.get_value(base_url_setting)
        if not base_url:
            raise ValueError("Base URL is not configured")

        headers = {}
        if provider.get("key_setting"):
            api_key = await self.get_value(provider["key_setting"])
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

        base_url = base_url.rstrip("/")
        if provider_id == "ollama":
            url = f"{base_url}/api/tags"
        else:
            url = f"{base_url}/models"

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            if provider_id == "ollama":
                return [m["name"] for m in data.get("models", [])]
            else:
                return [m["id"] for m in data.get("data", [])]

    # ─── Internal ─────────────────────────────────────────────────────────────

    async def _build_provider_infos(self, db_values: dict[str, str | None]) -> list[ProviderInfo]:
        """Build ProviderInfo list with is_configured and selected_model resolved."""
        infos: list[ProviderInfo] = []
        for p in _PROVIDERS:
            is_configured = False
            key_setting = p.get("key_setting")
            model_setting = p.get("model_setting")

            if not p["requires_key"]:
                # Ollama — always considered configured (local)
                is_configured = True
            elif key_setting:
                # Check DB first, then env
                value = db_values.get(key_setting)
                if not value and key_setting in _ENV_FALLBACKS:
                    value = getattr(env_settings, _ENV_FALLBACKS[key_setting], None) or None
                is_configured = bool(value and value.strip())

            # Resolve selected_model (never a secret — return as-is)
            selected_model: str | None = None
            if model_setting:
                selected_model = db_values.get(model_setting) or None

            base_url_setting = p.get("base_url_setting")
            selected_base_url: str | None = None
            if base_url_setting:
                val = db_values.get(base_url_setting)
                if not val and base_url_setting in _ENV_FALLBACKS:
                    val = getattr(env_settings, _ENV_FALLBACKS[base_url_setting], None) or None
                selected_base_url = val

            infos.append(
                ProviderInfo(
                    id=p["id"],
                    name=p["name"],
                    description=p["description"],
                    key_setting=key_setting,
                    model_setting=model_setting,
                    base_url_setting=base_url_setting,
                    selected_base_url=selected_base_url,
                    supports_fetch_models=p.get("supports_fetch_models", False),
                    requires_key=p["requires_key"],
                    is_configured=is_configured,
                    selected_model=selected_model,
                )
            )
        return infos


# ─── Provider probe (sync — runs in threadpool) ───────────────────────────────


def _probe_provider(provider_id: str, api_key: str | None) -> dict[str, Any]:
    """
    Run a minimal LiteLLM probe to verify the provider is reachable.
    Runs synchronously — call via asyncio.to_thread().
    """
    import litellm

    # Map provider_id → LiteLLM model string for a cheap ping
    probe_models: dict[str, str] = {
        "openai": "openai/gpt-4o-mini",
        "anthropic": "anthropic/claude-3-haiku-20240307",
        "gemini": "gemini/gemini-1.5-flash-latest",
        "groq": "groq/llama3-8b-8192",
        "mistral": "mistral/mistral-small-latest",
        "openrouter": "openrouter/openai/gpt-3.5-turbo",
        "ollama": "ollama/gemma4:latest",
    }

    model = probe_models.get(provider_id)
    if not model:
        return {
            "success": False,
            "message": "No probe model configured for this provider.",
            "model_count": None,
        }

    try:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
        }
        if api_key:
            kwargs["api_key"] = api_key

        litellm.completion(**kwargs)
        return {
            "success": True,
            "message": f"Connected to {provider_id} successfully.",
            "model_count": None,
        }
    except Exception as exc:
        return {"success": False, "message": str(exc)[:300], "model_count": None}


async def hydrate_settings_from_db() -> None:
    """
    Load DB-persisted settings into the in-memory ``settings`` singleton.

    This ensures that provider/model/key changes saved via the Settings page
    survive server restarts and are picked up cleanly by background workers
    without requiring manual environment changes or restarts.
    """
    from app.config import settings as env_settings
    from app.database import async_session_factory
    from app.repositories.app_settings import app_settings_repo
    from app.schemas.settings import SettingKey

    try:
        async with async_session_factory() as db:
            all_keys = [k.value for k in SettingKey]
            db_values = await app_settings_repo.get_many(db, all_keys)

            applied = 0
            for setting_key, value in db_values.items():
                if not value or not value.strip():
                    continue
                env_attr = _ENV_FALLBACKS.get(setting_key)
                if env_attr and hasattr(env_settings, env_attr):
                    object.__setattr__(env_settings, env_attr, value)
                    applied += 1

            if applied:
                log.info(
                    "settings_hydrated_from_db",
                    count=applied,
                    active_provider=env_settings.ACTIVE_PROVIDER,
                )
    except Exception as exc:
        log.warning(
            "settings_hydration_failed",
            error=str(exc),
            msg="DB settings could not be loaded — using .env defaults",
        )


def hydrate_settings_from_db_sync() -> None:
    """
    Synchronous wrapper for hydrate_settings_from_db().
    Safe to call in synchronous hooks like Celery worker_process_init or Task.before_start.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(hydrate_settings_from_db())
            return
    except RuntimeError:
        pass
    asyncio.run(hydrate_settings_from_db())
