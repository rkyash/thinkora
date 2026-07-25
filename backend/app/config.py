"""
Application configuration via pydantic-settings.
All environment variables are typed and validated at startup.
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Server ───────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-this-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    AUTH_ENABLED: bool = False

    # ─── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/thinkora"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── Data Storage ─────────────────────────────────────────
    THINKORA_DATA_DIR: str = "~/.thinkora"
    STORAGE_BACKEND: str = "local"
    AWS_BUCKET_NAME: str = ""
    AWS_REGION: str = ""
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # ─── CORS ─────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:5173"

    # ─── Qdrant ───────────────────────────────────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""

    # ─── Embedding ────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # ─── Celery ───────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ─── File Uploads ─────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 200

    # ─── LLM Providers ───────────────────────────────────────
    ACTIVE_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # ─── Custom OpenAI-Compatible Proxy (e.g. NVIDIA NIM, vLLM, LM Studio) ──
    # Set OPENAI_PROXY_BASE_URL to route through any OpenAI-compatible endpoint.
    # The model string in DEFAULT_MODEL should use the "openai/" prefix when this is set.
    OPENAI_PROXY_BASE_URL: str = ""   # e.g. https://integrate.api.nvidia.com/v1
    OPENAI_PROXY_API_KEY: str = ""    # API key for the proxy endpoint

    # ─── LLM Defaults ─────────────────────────────────────────
    DEFAULT_MODEL: str = "ollama/gemma4:latest"
    OPENAI_MODEL: str = "openai/gpt-4o-mini"
    ANTHROPIC_MODEL: str = "anthropic/claude-3-haiku-20240307"
    GEMINI_MODEL: str = "gemini/gemini-1.5-flash-latest"
    GROQ_MODEL: str = "groq/llama-3.1-8b-instant"
    MISTRAL_MODEL: str = "mistral/mistral-small-latest"
    OPENROUTER_MODEL: str = "openrouter/openai/gpt-3.5-turbo"
    OLLAMA_MODEL: str = "ollama/gemma4:latest"
    OPENAI_PROXY_MODEL: str = ""

    # ─── Audio TTS ────────────────────────────────────────────
    TTS_PROVIDER: str = "openai"
    KOKORO_BASE_URL: str = "http://localhost:8880"
    ELEVENLABS_API_KEY: str = ""
    ENABLE_DOCS: bool = True

    # ─── Bootstrap ────────────────────────────────────────────
    THINKORA_SKIP_BOOTSTRAP: bool = False

    @property
    def data_dir(self) -> Path:
        """Resolved data directory path."""
        return Path(self.THINKORA_DATA_DIR).expanduser().resolve()

    @property
    def max_upload_bytes(self) -> int:
        """Max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_dev(self) -> bool:
        """Whether we're in development mode."""
        return self.RELOAD

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure log level is valid."""
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            msg = f"Invalid LOG_LEVEL: {v}. Must be one of {valid}"
            raise ValueError(msg)
        return upper


# Singleton instance — import this everywhere
settings = Settings()
