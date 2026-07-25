"""
Notes API — /api/v1/notebooks/{notebook_id}/notes

Endpoints:
  GET    /                    List notes (paginated)
  POST   /                    Create note
  GET    /{note_id}           Get note
  PUT    /{note_id}           Update note (title, content, backlinks)
  DELETE /{note_id}           Delete note
  POST   /{note_id}/summarize AI-summarize note content → returns summary string
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.user import User
from app.repositories import note_repo, notebook_repo, workspace_repo
from app.schemas.note import (
    NoteCreate,
    NoteResponse,
    NoteSummarizeRequest,
    NoteSummaryResponse,
    NoteUpdate,
)
from app.schemas.pagination import OffsetParams, get_offset_params
from app.schemas.response import ApiResponse, PaginatedResponse, ok, paginated
from app.services.study_tools import StudyToolsService

router = APIRouter(tags=["Notes"])


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _verify_notebook_access(notebook_id: str, db: AsyncSession, user: User):
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    workspace = await workspace_repo.get_or_404(db, str(notebook.workspace_id))
    if workspace.owner_id != user.id:
        raise PermissionDeniedError("You don't own this notebook")
    return notebook


async def _verify_note_access(note_id: str, notebook_id: str, db: AsyncSession, user: User):
    note = await note_repo.get_or_404(db, note_id)
    if str(note.notebook_id) != notebook_id:
        raise NotFoundError("Note", note_id)
    await _verify_notebook_access(notebook_id, db, user)
    return note


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "/notebooks/{notebook_id}/notes",
    response_model=PaginatedResponse[NoteResponse],
)
async def list_notes(
    notebook_id: UUID,
    offset_params: OffsetParams = Depends(get_offset_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all notes in a notebook with pagination."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    notes = await note_repo.list_by_notebook(
        db, str(notebook_id), offset=offset_params.offset, limit=offset_params.limit
    )
    total = await note_repo.count(db, notebook_id=str(notebook_id))
    return paginated(
        [NoteResponse.model_validate(n) for n in notes],
        total=total,
        offset=offset_params.offset,
        limit=offset_params.limit,
    )


@router.post(
    "/notebooks/{notebook_id}/notes",
    response_model=ApiResponse[NoteResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    notebook_id: UUID,
    payload: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new note in a notebook."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    note = await note_repo.create(
        db,
        {
            "notebook_id": str(notebook_id),
            "title": payload.title,
            "content": payload.content,
            "backlinks": None,
        },
    )
    return ok(NoteResponse.model_validate(note), "Note created")


@router.get(
    "/notes/{note_id}",
    response_model=ApiResponse[NoteResponse],
)
async def get_note(
    note_id: str,
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single note by ID."""
    note = await _verify_note_access(note_id, notebook_id, db, current_user)
    return ok(NoteResponse.model_validate(note))


@router.put(
    "/notes/{note_id}",
    response_model=ApiResponse[NoteResponse],
)
async def update_note(
    note_id: str,
    notebook_id: str,
    payload: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a note's title, content, or backlinks."""
    await _verify_note_access(note_id, notebook_id, db, current_user)
    update_data = payload.model_dump(exclude_unset=True)
    # Serialize backlinks to list of dicts
    if "backlinks" in update_data and update_data["backlinks"] is not None:
        update_data["backlinks"] = [b.model_dump() for b in payload.backlinks]  # type: ignore[union-attr]
    note = await note_repo.update(db, note_id, update_data)
    return ok(NoteResponse.model_validate(note), "Note updated")


@router.delete(
    "/notes/{note_id}",
    response_model=ApiResponse[None],
)
async def delete_note(
    note_id: str,
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a note."""
    await _verify_note_access(note_id, notebook_id, db, current_user)
    await note_repo.delete(db, note_id)
    return ok(None, "Note deleted")


@router.post(
    "/notes/{note_id}/summarize",
    response_model=ApiResponse[NoteSummaryResponse],
)
async def summarize_note(
    note_id: str,
    notebook_id: str,
    payload: NoteSummarizeRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI-summarize the content of a note using the configured LLM.
    Returns a summary string — does NOT modify the note in place.
    """
    note = await _verify_note_access(note_id, notebook_id, db, current_user)
    svc = StudyToolsService(db)
    summary = await svc.summarize_note(
        note_id=note_id,
        content=note.content or "",
        model=payload.model if payload else None,
    )
    return ok(NoteSummaryResponse(note_id=note_id, summary=summary))
