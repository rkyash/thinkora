"""
Celery application instance — Redis broker/backend configuration.

Usage:
    celery -A app.workers.celery_app worker --loglevel=info

The Celery app uses separate Redis databases for broker (db 1) and
result backend (db 2) to isolate task messages from cached results.
"""

from typing import Any

from celery import Celery
from celery.signals import worker_process_init

from app.config import settings


def create_celery_app() -> Celery:
    """
    Factory for the Celery application.

    Configures:
    - Redis as both broker and result backend
    - JSON serialization for tasks and results
    - Task acknowledgement after execution (late ack)
    - Worker prefetch multiplier of 1 for fair scheduling
    - Task result expiry of 24 hours
    - Automatic task module discovery
    """
    app = Celery(
        "thinkora",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    app.conf.update(
        # ─── Serialization ────────────────────────────────────
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        # ─── Reliability ──────────────────────────────────────
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_reject_on_worker_lost=True,
        # ─── Results ─────────────────────────────────────────
        result_expires=86400,  # 24 hours
        # ─── Task routing ────────────────────────────────────
        task_default_queue="default",
        # ─── Timezone ────────────────────────────────────────
        timezone="UTC",
        enable_utc=True,
        # ─── Worker ──────────────────────────────────────────
        worker_max_tasks_per_child=1000,
        worker_cancel_long_running_tasks_on_connection_loss=True,
        # ─── Task tracking ───────────────────────────────────
        task_track_started=True,
        task_send_sent_event=True,
    )

    # Auto-discover task modules within the workers package
    app.autodiscover_tasks(
        [
            "app.workers.ingestion_tasks",
            "app.workers.audio_tasks",
        ]
    )

    return app


# ─── Singleton Celery instance ───────────────────────────────
celery_app = create_celery_app()


@worker_process_init.connect
def on_worker_process_init(**kwargs: Any) -> None:
    """Hydrate settings from DB when a worker process initializes."""
    from app.services.settings import hydrate_settings_from_db_sync

    hydrate_settings_from_db_sync()


# ─── Verification task ──────────────────────────────────────
@celery_app.task(name="thinkora.test_add", bind=True, ignore_result=False)
def test_add(self, x: int, y: int) -> dict[str, Any]:
    """
    Smoke-test task to verify Celery workers are operational.

    Usage:
        from app.workers.celery_app import test_add
        result = test_add.delay(2, 3)
        result.get(timeout=10)  # → {"result": 5, "task_id": "..."}
    """
    return {
        "result": x + y,
        "task_id": self.request.id,
    }
