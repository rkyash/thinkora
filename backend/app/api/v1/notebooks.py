"""
Notebooks API — CRUD endpoints (nested under workspaces).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import PermissionDeniedError
from app.models.user import User
from app.repositories import notebook_repo, workspace_repo
from app.schemas.notebook import NotebookCreate, NotebookResponse, NotebookUpdate
from app.schemas.pagination import OffsetParams, get_offset_params
from app.schemas.response import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/workspaces/{workspace_id}/notebooks", tags=["Notebooks"])


async def _verify_workspace_ownership(
    workspace_id: str, db: AsyncSession, current_user: User
) -> None:
    """Verify the workspace exists and is owned by the current user."""
    workspace = await workspace_repo.get_or_404(db, workspace_id)
    if workspace.owner_id != current_user.id:
        raise PermissionDeniedError("You don't own this workspace")


@router.get("", response_model=PaginatedResponse[NotebookResponse])
async def list_notebooks(
    workspace_id: str,
    offset_params: OffsetParams = Depends(get_offset_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notebooks in a workspace."""
    await _verify_workspace_ownership(workspace_id, db, current_user)
    notebooks = await notebook_repo.list_by_workspace(
        db, workspace_id, offset=offset_params.offset, limit=offset_params.limit
    )
    total = await notebook_repo.count(db, workspace_id=workspace_id)
    return {
        "success": True,
        "data": [NotebookResponse.model_validate(n) for n in notebooks],
        "total": total,
        "offset": offset_params.offset,
        "limit": offset_params.limit,
        "has_next": (offset_params.offset + offset_params.limit) < total,
    }


@router.post("", response_model=ApiResponse[NotebookResponse], status_code=201)
async def create_notebook(
    workspace_id: str,
    data: NotebookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new notebook in the workspace."""
    await _verify_workspace_ownership(workspace_id, db, current_user)
    notebook = await notebook_repo.create(db, {
        "workspace_id": workspace_id,
        "name": data.name,
        "description": data.description,
        "emoji": data.emoji,
    })
    return {
        "success": True,
        "data": NotebookResponse.model_validate(notebook),
        "message": "Notebook created",
    }


@router.get("/{notebook_id}", response_model=ApiResponse[NotebookResponse])
async def get_notebook(
    workspace_id: str,
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a notebook by ID."""
    await _verify_workspace_ownership(workspace_id, db, current_user)
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    return {
        "success": True,
        "data": NotebookResponse.model_validate(notebook),
    }


@router.put("/{notebook_id}", response_model=ApiResponse[NotebookResponse])
@router.patch("/{notebook_id}", response_model=ApiResponse[NotebookResponse])
async def update_notebook(
    workspace_id: str,
    notebook_id: str,
    data: NotebookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update notebook name, emoji, or description."""
    await _verify_workspace_ownership(workspace_id, db, current_user)
    update_data = data.model_dump(exclude_unset=True)
    notebook = await notebook_repo.update(db, notebook_id, update_data)
    return {
        "success": True,
        "data": NotebookResponse.model_validate(notebook),
        "message": "Notebook updated",
    }


@router.delete("/{notebook_id}", response_model=ApiResponse)
async def delete_notebook(
    workspace_id: str,
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a notebook and all its contents (sources, chunks, Qdrant collection)."""
    await _verify_workspace_ownership(workspace_id, db, current_user)
    # TODO: Also drop Qdrant collection when vector_store service is ready
    await notebook_repo.delete(db, notebook_id)
    return {
        "success": True,
        "data": None,
        "message": "Notebook deleted",
    }


# ─── Direct Notebook Endpoints (Non-nested) ─────────────────────────
router_direct = APIRouter(prefix="/notebooks", tags=["Notebooks Direct"])


async def _verify_notebook_ownership(
    notebook_id: str, db: AsyncSession, current_user: User
):
    """Verify the notebook exists and belongs to a workspace owned by the current user."""
    from app.models.notebook import Notebook
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    workspace = await workspace_repo.get_or_404(db, notebook.workspace_id)
    if not workspace or workspace.owner_id != current_user.id:
        raise PermissionDeniedError("You don't own this notebook")
    return notebook


@router_direct.get("/{notebook_id}", response_model=ApiResponse[NotebookResponse])
async def get_notebook_direct(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a notebook by ID without nested workspace path."""
    notebook = await _verify_notebook_ownership(notebook_id, db, current_user)
    return {
        "success": True,
        "data": NotebookResponse.model_validate(notebook),
    }


@router_direct.put("/{notebook_id}", response_model=ApiResponse[NotebookResponse])
@router_direct.patch("/{notebook_id}", response_model=ApiResponse[NotebookResponse])
async def update_notebook_direct(
    notebook_id: str,
    data: NotebookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a notebook by ID without nested workspace path."""
    await _verify_notebook_ownership(notebook_id, db, current_user)
    update_data = data.model_dump(exclude_unset=True)
    notebook = await notebook_repo.update(db, notebook_id, update_data)
    return {
        "success": True,
        "data": NotebookResponse.model_validate(notebook),
        "message": "Notebook updated",
    }


@router_direct.delete("/{notebook_id}", response_model=ApiResponse)
async def delete_notebook_direct(
    notebook_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a notebook by ID without nested workspace path."""
    await _verify_notebook_ownership(notebook_id, db, current_user)
    await notebook_repo.delete(db, notebook_id)
    return {
        "success": True,
        "data": None,
        "message": "Notebook deleted",
    }