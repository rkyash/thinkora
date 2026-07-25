"""
Celery tasks for audio generation pipeline (Podcast).
"""

import asyncio
from typing import Any

import structlog

from app.core.constants import TaskStatus
from app.database import async_session_factory
from app.repositories import generation_repo
from app.services.audio import AudioService
from app.services.notification import publish_event
from app.workers.base_task import BaseTask
from app.workers.celery_app import celery_app

logger = structlog.get_logger()


@celery_app.task(base=BaseTask, bind=True, name="thinkora.generate_podcast")
def generate_podcast_task(
    self,
    notebook_id: str,
    generation_id: str,
    tts_backend: str = "gtts",
    model: str | None = None,
) -> dict[str, Any]:
    """
    Celery task to generate a multi-speaker podcast audio.
    """
    logger.info(
        "generate_podcast_task_started",
        task_name=self.name,
        task_id=self.request.id,
        notebook_id=notebook_id,
        generation_id=generation_id,
    )

    async def _run_podcast() -> dict[str, Any]:
        async with async_session_factory() as session:
            try:
                # Initialize audio service
                audio_service = AudioService(session)

                # Generate the podcast audio (this also publishes SSE events)
                saved_path = await audio_service.generate_podcast(
                    notebook_id=notebook_id,
                    generation_id=generation_id,
                    tts_backend=tts_backend,
                    model=model,
                )

                # Update the generation record to complete
                await generation_repo.update(
                    session,
                    generation_id,
                    {
                        "status": TaskStatus.READY,
                        "audio_path": saved_path,
                    }
                )
                # Commit the transaction to save status
                await session.commit()

                return {
                    "status": "completed",
                    "notebook_id": notebook_id,
                    "generation_id": generation_id,
                    "audio_path": saved_path,
                    "task_id": self.request.id,
                }
            except Exception as e:
                # Update status to error and persist exact error message
                await generation_repo.update(
                    session,
                    generation_id,
                    {
                        "status": TaskStatus.ERROR,
                        "content": {"error_msg": str(e)},
                    },
                )
                await session.commit()
                
                # Publish error event to notify client
                await publish_event(
                    generation_id,
                    {
                        "status": "error",
                        "step": "error",
                        "detail": {"error_msg": str(e)},
                    }
                )
                
                raise

    return asyncio.run(_run_podcast())
