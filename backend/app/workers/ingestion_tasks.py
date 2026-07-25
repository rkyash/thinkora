"""
Celery tasks for document ingestion pipeline.

All tasks inherit from BaseTask for consistent error handling, logging, and retries.
"""

import asyncio
from typing import Any

import structlog

from app.database import async_session_factory
from app.services.ingestion import IngestionService
from app.workers.base_task import BaseTask
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(base=BaseTask, bind=True, name="thinkora.ingest_source")
def ingest_source_task(self, source_id: str) -> dict[str, Any]:
    """
    Celery task to run the full ingestion pipeline for a source.

    This task:
    1. Creates an async database session
    2. Instantiates the IngestionService
    3. Runs the full pipeline: fetch → parse → chunk → embed → store → persist → notify
    4. Updates source status throughout the process

    Args:
        source_id: The UUID of the source to ingest

    Returns:
        Dict with status and metadata about the ingestion

    Raises:
        Exception: Propagates any errors for retry handling by BaseTask
    """
    logger.info(
        "ingestion_task_started",
        task_name=self.name,
        task_id=self.request.id,
        source_id=source_id,
    )

    # Create async database session
    async def _run_ingestion():
        async with async_session_factory() as session:
            # Initialize ingestion service with DB session
            ingestion_service = IngestionService(session)

            # Run the full ingestion pipeline
            await ingestion_service.ingest_source(source_id)

            # Return success metrics
            return {
                "status": "completed",
                "source_id": source_id,
                "task_id": self.request.id,
            }

    # Run the async function and return result
    return asyncio.run(_run_ingestion())