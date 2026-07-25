"""
CORS configuration from settings.
"""

from starlette.middleware.cors import CORSMiddleware

from app.config import settings


def get_cors_origins() -> list[str]:
    """Get allowed CORS origins from config."""
    origins = [settings.FRONTEND_URL]
    # In dev, also allow common local ports
    if settings.is_dev:
        origins.extend([
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
        ])
    return list(set(origins))


# CORS config dict — applied in main.py
CORS_CONFIG = {
    "allow_origins": get_cors_origins(),
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["X-Request-ID", "X-Process-Time"],
}
