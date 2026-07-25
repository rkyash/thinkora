"""
Application shutdown hooks — clean up resources.
"""

from app.bootstrap.worker import stop_worker
from app.core.cache import close_redis
from app.core.logging import logger
from app.database import engine


async def on_shutdown() -> None:
    """
    Shutdown tasks:
    1. Stop Celery worker subprocess
    2. Close database connection pool
    3. Close Redis connection
    """
    # 1. Stop managed Celery worker
    stop_worker()

    # 2. Close SQLAlchemy engine
    await engine.dispose()
    logger.info("database_connections_closed")

    # 3. Close Redis
    await close_redis()
    logger.info("redis_connection_closed")

    logger.info("app_shutdown_complete")
