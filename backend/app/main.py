"""
Thinkora — FastAPI application factory.
Mounts routers, registers middleware, configures lifespan events.
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.constants import API_V1_PREFIX, APP_NAME
from app.core.exceptions import AppError
from app.events.startup import on_startup
from app.events.shutdown import on_shutdown
from app.middlewares.cors import CORS_CONFIG
from app.middlewares.request_id import RequestIDMiddleware
from app.middlewares.timing import TimingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown hooks."""
    await on_startup()
    yield
    await on_shutdown()


def create_app() -> FastAPI:
    """FastAPI application factory."""

    application = FastAPI(
        title=APP_NAME,
        description="Local-first document chat application — thinkora/NotebookLM alternative",
        version="0.1.0",
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
        lifespan=lifespan,
    )

    # ─── Middleware (order matters: last added = first executed) ───
    # CORS must be outermost
    application.add_middleware(CORSMiddleware, **CORS_CONFIG)

    # Timing (wraps everything after CORS)
    application.add_middleware(TimingMiddleware)

    # Request ID (innermost — runs first, sets context)
    application.add_middleware(RequestIDMiddleware)

    # ─── Exception handlers ──────────────────────────────────────

    @application.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle custom application errors with consistent envelope."""
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.error,
                "code": exc.code,
                "request_id": request_id,
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions."""
        from app.core.logging import logger

        request_id = getattr(request.state, "request_id", None)
        logger.error("unhandled_exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "code": "INTERNAL_ERROR",
                "request_id": request_id,
            },
        )

    # ─── Health \u0026 Readiness probes ──────────────────────────────────────────

    @application.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Liveness probe — returns 200 if the process is alive."""
        from datetime import datetime, timezone
        return {
            "status": "ok",
            "service": APP_NAME,
            "version": "0.1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @application.get("/readyz", tags=["Health"])
    async def readiness_check() -> dict:
        """
        Readiness probe — checks all critical dependencies.
        Returns 200 when PostgreSQL, Redis, and Qdrant are reachable.
        Returns 503 when any dependency is unhealthy.
        """
        import asyncio
        from fastapi.responses import JSONResponse

        deps: dict[str, str] = {}

        # ── PostgreSQL ────────────────────────────────────────────
        try:
            from app.database import async_session_factory
            from sqlalchemy import text as sa_text
            async with async_session_factory() as session:
                await session.execute(sa_text("SELECT 1"))
            deps["postgres"] = "ok"
        except Exception as exc:
            deps["postgres"] = f"error: {exc}"

        # ── Redis ─────────────────────────────────────────────────
        try:
            from app.config import settings
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            await r.ping()
            await r.aclose()
            deps["redis"] = "ok"
        except Exception as exc:
            deps["redis"] = f"error: {exc}"

        # ── Qdrant ────────────────────────────────────────────────
        try:
            from app.config import settings
            from qdrant_client import AsyncQdrantClient
            qdrant_url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
            qc = AsyncQdrantClient(url=qdrant_url, timeout=3)
            await qc.get_collections()
            await qc.close()
            deps["qdrant"] = "ok"
        except Exception as exc:
            deps["qdrant"] = f"error: {exc}"

        all_ok = all(v == "ok" for v in deps.values())
        status_code = 200 if all_ok else 503
        return JSONResponse(
            status_code=status_code,
            content={"status": "ready" if all_ok else "degraded", "dependencies": deps},
        )

    # ─── Mount API routers ────────────────────────────────────────
    from app.api.router import api_router
    application.include_router(api_router, prefix=API_V1_PREFIX)

    return application


# Application instance — imported by uvicorn
app = create_app()
