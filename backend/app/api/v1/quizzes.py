"""
Quizzes API — /api/v1/notebooks/{notebook_id}/quizzes

Endpoints:
  GET    /              List quizzes (paginated)
  POST   /generate      AI-generate a quiz with questions
  GET    /{quiz_id}     Get quiz + all questions
  DELETE /{quiz_id}     Delete quiz + cascade questions
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.user import User
from app.repositories import quiz_repo, notebook_repo, workspace_repo
from app.schemas.quiz import (
    QuizDetailResponse,
    QuizGenerateRequest,
    QuizQuestionResponse,
    QuizResponse,
)
from app.schemas.pagination import OffsetParams, get_offset_params
from app.schemas.response import ApiResponse, PaginatedResponse, ok, paginated
from app.services.study_tools import StudyToolsService

router = APIRouter(tags=["Quizzes"])


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _verify_notebook_access(notebook_id: str, db: AsyncSession, user: User):
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    workspace = await workspace_repo.get_or_404(db, str(notebook.workspace_id))
    if workspace.owner_id != user.id:
        raise PermissionDeniedError("You don't own this notebook")
    return notebook


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "/notebooks/{notebook_id}/quizzes",
    response_model=PaginatedResponse[QuizResponse],
)
async def list_quizzes(
    notebook_id: UUID,
    offset_params: OffsetParams = Depends(get_offset_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all quizzes in a notebook with pagination."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    quizzes = await quiz_repo.list_by_notebook(
        db, str(notebook_id), offset=offset_params.offset, limit=offset_params.limit
    )
    total = await quiz_repo.count(db, notebook_id=str(notebook_id))
    return paginated(
        [QuizResponse.model_validate(q) for q in quizzes],
        total=total,
        offset=offset_params.offset,
        limit=offset_params.limit,
    )


@router.post(
    "/notebooks/{notebook_id}/quizzes/generate",
    response_model=ApiResponse[QuizDetailResponse],
    status_code=status.HTTP_201_CREATED,
)
async def generate_quiz(
    notebook_id: UUID,
    payload: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI-generate a quiz with questions from the notebook's source material.
    Returns the full quiz with all questions included.
    """
    await _verify_notebook_access(str(notebook_id), db, current_user)
    svc = StudyToolsService(db)
    quiz = await svc.generate_quiz(
        notebook_id=str(notebook_id),
        title=payload.title,
        question_count=payload.question_count,
        question_types=payload.question_types,
        topic=payload.topic,
        model=payload.model,
    )
    return ok(
        QuizDetailResponse(
            id=str(quiz.id),
            notebook_id=str(quiz.notebook_id),
            title=quiz.title,
            created_at=quiz.created_at,
            questions=[QuizQuestionResponse.model_validate(q) for q in (quiz.questions or [])],
        ),
        "Quiz generated successfully",
    )


@router.get(
    "/notebooks/{notebook_id}/quizzes/{quiz_id}",
    response_model=ApiResponse[QuizDetailResponse],
)
async def get_quiz(
    notebook_id: UUID,
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a quiz with all its questions."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    quiz = await quiz_repo.get_with_questions(db, quiz_id)
    if quiz is None or str(quiz.notebook_id) != str(notebook_id):
        raise NotFoundError("Quiz", quiz_id)
    return ok(
        QuizDetailResponse(
            id=str(quiz.id),
            notebook_id=str(quiz.notebook_id),
            title=quiz.title,
            created_at=quiz.created_at,
            questions=[QuizQuestionResponse.model_validate(q) for q in (quiz.questions or [])],
        )
    )


@router.delete(
    "/notebooks/{notebook_id}/quizzes/{quiz_id}",
    response_model=ApiResponse[None],
)
async def delete_quiz(
    notebook_id: UUID,
    quiz_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a quiz and all its questions (cascade)."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    quiz = await quiz_repo.get_or_404(db, quiz_id)
    if str(quiz.notebook_id) != str(notebook_id):
        raise NotFoundError("Quiz", quiz_id)
    await quiz_repo.delete(db, quiz_id)
    return ok(None, "Quiz deleted")
