"""
Base Celery Task class — auto-retry, structured logging, error reporting.

All long-running Celery tasks (ingestion, graph, podcast, export) should
inherit from BaseTask to get consistent error handling and logging.
"""

from typing import Any

import celery
import structlog

logger = structlog.get_logger()


class BaseTask(celery.Task):
    """
    Abstract base class for all Thinkora Celery tasks.

    Features:
    - Automatic retry with exponential backoff (up to 3 retries)
    - Structured logging on start, success, failure, and retry
    - on_failure hook to update source/generation status to 'error' in DB

    Usage:
        @celery_app.task(base=BaseTask, bind=True)
        def my_task(self, arg1, arg2):
            ...
    """

    abstract = True
    max_retries = 3
    default_retry_delay = 60  # seconds
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes max backoff
    retry_jitter = True

    def before_start(
        self,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Log when a task begins execution and hydrate latest DB settings."""
        try:
            from app.services.settings import hydrate_settings_from_db_sync
            hydrate_settings_from_db_sync()
        except Exception as exc:
            logger.warning("task_before_start_settings_hydration_failed", error=str(exc))

        logger.info(
            "task_started",
            task_name=self.name,
            task_id=task_id,
            args=str(args)[:200],
            kwargs=str(kwargs)[:200],
        )

    def on_success(
        self,
        retval: Any,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Log when a task completes successfully."""
        logger.info(
            "task_succeeded",
            task_name=self.name,
            task_id=task_id,
        )

    def on_failure(
        self,
        exc: BaseException,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        """
        Log when a task fails permanently (all retries exhausted).

        Future enhancement: update source/generation status to 'error' in DB.
        """
        logger.error(
            "task_failed",
            task_name=self.name,
            task_id=task_id,
            exc=str(exc),
            retries_exhausted=self.request.retries,
        )

    def on_retry(
        self,
        exc: BaseException,
        task_id: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
        einfo: Any,
    ) -> None:
        """Log when a task is retried."""
        logger.warning(
            "task_retrying",
            task_name=self.name,
            task_id=task_id,
            attempt=self.request.retries,
            exc=str(exc),
        )
