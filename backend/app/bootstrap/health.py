"""
Service health checks — wait until all dependencies are ready.
"""

import asyncio
import time

from app.config import settings
from app.core.logging import logger


async def wait_for_all_services(
    timeout: int = 90,
    interval: float = 2.0,
) -> dict[str, bool]:
    """
    Wait until all required services pass health checks.
    Returns a dict of service_name -> healthy (bool).
    """
    deadline = time.monotonic() + timeout
    results: dict[str, bool] = {}

    checks = {
        "postgres": _check_postgres,
        "redis": _check_redis,
        "qdrant": _check_qdrant,
    }

    logger.info("bootstrap_health_waiting", msg="Waiting for services to become healthy...")

    while time.monotonic() < deadline:
        pending = {}
        for name, check_fn in checks.items():
            if results.get(name):
                continue  # already healthy
            try:
                healthy = await check_fn()
                if healthy:
                    results[name] = True
                    logger.info("bootstrap_service_healthy", service=name)
                else:
                    pending[name] = True
            except Exception:
                pending[name] = True

        if not pending:
            logger.info("bootstrap_all_healthy", msg="All services are healthy")
            return results

        remaining = int(deadline - time.monotonic())
        logger.info(
            "bootstrap_health_pending",
            waiting_for=list(pending.keys()),
            remaining_seconds=remaining,
        )
        await asyncio.sleep(interval)

    # Timed out — mark unhealthy services
    for name in checks:
        if name not in results:
            results[name] = False
            logger.error("bootstrap_service_unhealthy", service=name)

    return results


async def _check_postgres() -> bool:
    """Check PostgreSQL connectivity."""
    try:
        from sqlalchemy import text as sa_text
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(sa_text("SELECT 1"))
        await engine.dispose()
        return True
    except Exception:
        return False


async def _check_redis() -> bool:
    """Check Redis connectivity."""
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        pong = await r.ping()
        await r.aclose()
        return pong
    except Exception:
        return False


async def _check_qdrant() -> bool:
    """Check Qdrant connectivity."""
    try:
        from qdrant_client import AsyncQdrantClient
        url = f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        client = AsyncQdrantClient(url=url, timeout=5)
        await client.get_collections()
        await client.close()
        return True
    except Exception:
        return False
