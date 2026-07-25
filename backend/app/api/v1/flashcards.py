"""
Flashcards API — /api/v1/notebooks/{notebook_id}/flashcards

Endpoints:
  GET    /              List flashcards (paginated)
  POST   /              Manually create a flashcard
  POST   /generate      AI-generate flashcard set (synchronous, not Celery)
  DELETE /{card_id}     Delete a single flashcard
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.user import User
from app.repositories import flashcard_repo, notebook_repo, workspace_repo
from app.schemas.flashcard import (
    FlashcardCreate,
    FlashcardGenerateRequest,
    FlashcardResponse,
)
from app.schemas.pagination import OffsetParams, get_offset_params
from app.schemas.response import ApiResponse, PaginatedResponse, ok, paginated
from app.services.study_tools import StudyToolsService

router = APIRouter(tags=["Flashcards"])


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _verify_notebook_access(notebook_id: str, db: AsyncSession, user: User):
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    workspace = await workspace_repo.get_or_404(db, str(notebook.workspace_id))
    if workspace.owner_id != user.id:
        raise PermissionDeniedError("You don't own this notebook")
    return notebook


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "/notebooks/{notebook_id}/flashcards",
    response_model=PaginatedResponse[FlashcardResponse],
)
async def list_flashcards(
    notebook_id: UUID,
    offset_params: OffsetParams = Depends(get_offset_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all flashcards in a notebook with pagination."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    cards = await flashcard_repo.list_by_notebook(
        db, str(notebook_id), offset=offset_params.offset, limit=offset_params.limit
    )
    total = await flashcard_repo.count(db, notebook_id=str(notebook_id))
    return paginated(
        [FlashcardResponse.model_validate(c) for c in cards],
        total=total,
        offset=offset_params.offset,
        limit=offset_params.limit,
    )


@router.post(
    "/notebooks/{notebook_id}/flashcards",
    response_model=ApiResponse[FlashcardResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_flashcard(
    notebook_id: UUID,
    payload: FlashcardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually create a single flashcard in a notebook."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    card = await flashcard_repo.create(
        db,
        {
            "notebook_id": str(notebook_id),
            "question": payload.question,
            "answer": payload.answer,
            "difficulty": payload.difficulty,
        },
    )
    return ok(FlashcardResponse.model_validate(card), "Flashcard created")


@router.post(
    "/notebooks/{notebook_id}/flashcards/generate",
    response_model=ApiResponse[list[FlashcardResponse]],
)
async def generate_flashcards(
    notebook_id: UUID,
    payload: FlashcardGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI-generate a set of flashcards from the notebook's source material.
    Runs synchronously;later for large notebooks, consider using a background task or Celery for async processing.
    """
    await _verify_notebook_access(str(notebook_id), db, current_user)
    svc = StudyToolsService(db)
    cards = await svc.generate_flashcards(
        notebook_id=str(notebook_id),
        count=payload.count,
        difficulty=payload.difficulty,
        topic=payload.topic,
        model=payload.model,
    )
    return ok(
        [FlashcardResponse.model_validate(c) for c in cards],
        f"Generated {len(cards)} flashcards",
    )


@router.delete(
    "/notebooks/{notebook_id}/flashcards/{card_id}",
    response_model=ApiResponse[None],
)
async def delete_flashcard(
    notebook_id: UUID,
    card_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a single flashcard."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    card = await flashcard_repo.get_or_404(db, card_id)
    if str(card.notebook_id) != str(notebook_id):
        raise NotFoundError("Flashcard", card_id)
    await flashcard_repo.delete(db, card_id)
    return ok(None, "Flashcard deleted")
