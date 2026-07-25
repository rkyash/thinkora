"""
Generate API — /api/v1/notebooks/{notebook_id}/generate

Endpoints:
  POST   /summary        AI-summarize all sources in the notebook
  POST   /study-guide    Generate a structured study guide markdown document
  GET    /history        List past generations for a notebook
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import PermissionDeniedError
from app.models.user import User
from app.repositories import generation_repo, notebook_repo, workspace_repo
from app.schemas.generation import GenerationRequest, GenerationResponse
from app.schemas.pagination import OffsetParams, get_offset_params
from app.schemas.response import ApiResponse, PaginatedResponse, ok, paginated
from app.services.study_tools import StudyToolsService

router = APIRouter(tags=["Generate"])


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _verify_notebook_access(notebook_id: str, db: AsyncSession, user: User):
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    workspace = await workspace_repo.get_or_404(db, str(notebook.workspace_id))
    if workspace.owner_id != user.id:
        raise PermissionDeniedError("You don't own this notebook")
    return notebook


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.post(
    "/notebooks/{notebook_id}/generate/summary",
    response_model=ApiResponse[GenerationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_summary(
    notebook_id: UUID,
    payload: GenerationRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a comprehensive markdown summary of all sources in the notebook.
    Persists the result as a Generation record (type=summary).
    """
    await _verify_notebook_access(str(notebook_id), db, current_user)
    svc = StudyToolsService(db)
    generation = await svc.generate_summary(
        notebook_id=str(notebook_id),
        model=payload.model if payload else None,
    )
    return ok(GenerationResponse.model_validate(generation), "Summary generated")


@router.post(
    "/notebooks/{notebook_id}/generate/study-guide",
    response_model=ApiResponse[GenerationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_study_guide(
    notebook_id: UUID,
    payload: GenerationRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a structured study guide from the notebook's source material.
    Persists the result as a Generation record (type=study_guide).
    """
    notebook = await _verify_notebook_access(str(notebook_id), db, current_user)
    svc = StudyToolsService(db)
    generation = await svc.generate_study_guide(
        notebook_id=str(notebook_id),
        notebook_name=notebook.name,
        model=payload.model if payload else None,
    )
    return ok(GenerationResponse.model_validate(generation), "Study guide generated")


@router.get(
    "/notebooks/{notebook_id}/generate/history",
    response_model=PaginatedResponse[GenerationResponse],
)
async def list_generations(
    notebook_id: UUID,
    offset_params: OffsetParams = Depends(get_offset_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all past generations (summaries, study guides, etc.) for a notebook."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    generations = await generation_repo.list_all(
        db,
        notebook_id=str(notebook_id),
        offset=offset_params.offset,
        limit=offset_params.limit,
    )
    total = await generation_repo.count(db, notebook_id=str(notebook_id))
    return paginated(
        [GenerationResponse.model_validate(g) for g in generations],
        total=total,
        offset=offset_params.offset,
        limit=offset_params.limit,
    )
