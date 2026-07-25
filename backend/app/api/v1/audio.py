"""
Audio/Podcast API — /api/v1/notebooks/{notebook_id}/audio
"""

from typing import Optional

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import GenerationType, TaskStatus
from app.core.dependencies import get_current_user, get_current_user_for_sse, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.user import User
from app.repositories import generation_repo, notebook_repo, workspace_repo
from app.schemas.audio import AudioGenerateRequest, AudioStatusResponse
from app.schemas.generation import GenerationResponse
from app.schemas.response import ApiResponse, ok
from app.services.storage import LocalStorage, get_storage
from app.workers.audio_tasks import generate_podcast_task

router = APIRouter(tags=["Audio"])


async def _verify_notebook_access(notebook_id: str, db: AsyncSession, user: User):
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    workspace = await workspace_repo.get_or_404(db, str(notebook.workspace_id))
    if workspace.owner_id != user.id:
        raise PermissionDeniedError("You don't own this notebook")
    return notebook


@router.post(
    "/notebooks/{notebook_id}/audio",
    response_model=ApiResponse[GenerationResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_audio(
    notebook_id: str,
    payload: AudioGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a Celery task to generate a podcast for the notebook."""
    await _verify_notebook_access(notebook_id, db, current_user)
    
    # Check if a podcast generation is already running for this notebook
    existing = await generation_repo.list_by_type(db, notebook_id, GenerationType.PODCAST, limit=1)
    if existing and existing[0].status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
        return ok(GenerationResponse.model_validate(existing[0]), "Podcast generation already in progress")

    # Create generation record
    gen = await generation_repo.create(
        db,
        {
            "notebook_id": notebook_id,
            "type": GenerationType.PODCAST,
            "status": TaskStatus.PENDING,
        },
    )
    
    # Trigger Celery task
    task = generate_podcast_task.delay(
        notebook_id=notebook_id,
        generation_id=str(gen.id),
        tts_backend=payload.tts_backend,
        model=payload.model,
    )
    
    # Save task_id in record
    gen = await generation_repo.update(db, str(gen.id), {"task_id": task.id})
    
    return ok(GenerationResponse.model_validate(gen), "Podcast generation started")


@router.get(
    "/notebooks/{notebook_id}/audio/status",
    response_model=ApiResponse[AudioStatusResponse],
)
async def get_audio_status(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check the status of the most recent podcast generation for a notebook."""
    await _verify_notebook_access(notebook_id, db, current_user)
    
    existing = await generation_repo.list_by_type(db, notebook_id, GenerationType.PODCAST, limit=1)
    if not existing:
        raise NotFoundError("Podcast Generation", notebook_id)
        
    gen = existing[0]
    audio_url = f"/api/v1/notebooks/{notebook_id}/audio/stream" if gen.status == TaskStatus.READY else None
    
    resp = AudioStatusResponse(
        generation=GenerationResponse.model_validate(gen),
        audio_url=audio_url
    )
    return ok(resp)


@router.get(
    "/notebooks/{notebook_id}/audio/stream",
)
async def stream_audio(
    notebook_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_for_sse),
):
    """Stream the generated podcast MP3 with Range support."""
    await _verify_notebook_access(notebook_id, db, current_user)
    
    existing = await generation_repo.list_by_type(db, notebook_id, GenerationType.PODCAST, limit=1)
    if not existing:
        raise NotFoundError("Podcast Generation", notebook_id)
        
    gen = existing[0]
    if gen.status != TaskStatus.READY or not gen.audio_path:
        raise NotFoundError("Podcast Audio", notebook_id)
        
    storage = get_storage()
    if not await storage.exists(gen.audio_path):
        raise NotFoundError("Podcast File", gen.audio_path)
        
    # Range support via FileResponse if using LocalStorage
    if isinstance(storage, LocalStorage):
        file_path = storage._resolve(gen.audio_path)
        return FileResponse(
            path=file_path,
            media_type="audio/mpeg",
            headers={"Accept-Ranges": "bytes"}
        )
    
    # Fallback for other storage backends (no Range support)
    data = await storage.load(gen.audio_path)
    return Response(content=data, media_type="audio/mpeg")


@router.delete(
    "/notebooks/{notebook_id}/audio",
    response_model=ApiResponse[None],
)
async def delete_audio(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete the podcast generation and its audio file."""
    await _verify_notebook_access(notebook_id, db, current_user)
    
    existing = await generation_repo.list_by_type(db, notebook_id, GenerationType.PODCAST, limit=1)
    if not existing:
        raise NotFoundError("Podcast Generation", notebook_id)
        
    gen = existing[0]
    
    # Delete from storage
    if gen.audio_path:
        storage = get_storage()
        if await storage.exists(gen.audio_path):
            await storage.delete(gen.audio_path)
            
    # Delete from database
    await generation_repo.delete(db, str(gen.id))
    
    return ok(None, "Podcast deleted")
