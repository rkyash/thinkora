"""
Application startup hooks — run before the first request.
"""

from app.bootstrap import run_bootstrap
from app.config import settings
from app.core.cache import get_redis, redis_ping
from app.core.logging import logger


async def on_startup() -> None:
    """
    Startup tasks:
    0. Auto-bootstrap (Docker, migrations, workers)
    0.5. Hydrate in-memory settings from DB overrides
    1. Ensure data directory exists
    2. Ping Redis
    3. Log startup info
    """
    # 0. Auto-bootstrap — detects and provisions infrastructure
    await run_bootstrap()

    # 0.5. Hydrate in-memory settings from DB overrides
    # Must run AFTER bootstrap (migrations ensure app_settings table exists)
    await _hydrate_settings_from_db()

    # 1. Create data directory
    data_dir = settings.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "uploads").mkdir(exist_ok=True)
    (data_dir / "audio").mkdir(exist_ok=True)
    (data_dir / "exports").mkdir(exist_ok=True)
    logger.info("data_directory_ready", path=str(data_dir))

    # 2. Redis health check
    redis_ok = await redis_ping()
    if redis_ok:
        logger.info("redis_connected", url=settings.REDIS_URL)
    else:
        logger.warning("redis_unavailable", url=settings.REDIS_URL)

    # 3. Celery broker health check
    try:
        from app.workers.celery_app import celery_app
        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1, timeout=5)
        conn.close()
        logger.info(
            "celery_broker_connected",
            broker=settings.CELERY_BROKER_URL,
            backend=settings.CELERY_RESULT_BACKEND,
        )
    except Exception as e:
        logger.warning(
            "celery_broker_unavailable",
            broker=settings.CELERY_BROKER_URL,
            error=str(e),
        )

    # 4. Log startup info
    logger.info(
        "app_starting",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL,
        database=settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "***",
    )

    # 5. Create default local user if Auth is disabled
    if not settings.AUTH_ENABLED:
        from app.database import async_session_factory
        from app.repositories import user_repo
        async with async_session_factory() as db:
            user = await user_repo.get_by_email(db, "local@thinkora.app")
            if not user:
                await user_repo.create(
                    db,
                    {
                        "email": "local@thinkora.app",
                        "username": "Local User",
                        "hashed_password": "disabled",
                        "is_active": True,
                    },
                )
                await db.commit()
                logger.info("local_user_created", email="local@thinkora.app")


async def _hydrate_settings_from_db() -> None:
    """Delegate settings hydration to the settings service."""
    from app.services.settings import hydrate_settings_from_db
    await hydrate_settings_from_db()


