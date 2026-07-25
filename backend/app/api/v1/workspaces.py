"""
Workspaces API — CRUD endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.user import User
from app.repositories import workspace_repo
from app.schemas.pagination import OffsetParams, get_offset_params
from app.schemas.response import ApiResponse, PaginatedResponse
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("", response_model=PaginatedResponse[WorkspaceResponse])
async def list_workspaces(
    offset_params: OffsetParams = Depends(get_offset_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List workspaces owned by the current user."""
    workspaces = await workspace_repo.list_by_owner(
        db, current_user.id, offset=offset_params.offset, limit=offset_params.limit
    )
    total = await workspace_repo.count(db, owner_id=current_user.id)
    return {
        "success": True,
        "data": [WorkspaceResponse.model_validate(w) for w in workspaces],
        "total": total,
        "offset": offset_params.offset,
        "limit": offset_params.limit,
        "has_next": (offset_params.offset + offset_params.limit) < total,
    }


@router.post("", response_model=ApiResponse[WorkspaceResponse], status_code=201)
async def create_workspace(
    data: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new workspace."""
    workspace = await workspace_repo.create(db, {
        "owner_id": current_user.id,
        "name": data.name,
        "description": data.description,
    })
    return {
        "success": True,
        "data": WorkspaceResponse.model_validate(workspace),
        "message": "Workspace created",
    }


@router.get("/{workspace_id}", response_model=ApiResponse[WorkspaceResponse])
async def get_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a workspace by ID."""
    workspace = await workspace_repo.get_or_404(db, workspace_id)
    if workspace.owner_id != current_user.id:
        raise PermissionDeniedError("You don't own this workspace")
    return {
        "success": True,
        "data": WorkspaceResponse.model_validate(workspace),
    }


@router.put("/{workspace_id}", response_model=ApiResponse[WorkspaceResponse])
@router.patch("/{workspace_id}", response_model=ApiResponse[WorkspaceResponse])
async def update_workspace(
    workspace_id: str,
    data: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a workspace."""
    workspace = await workspace_repo.get_or_404(db, workspace_id)
    if workspace.owner_id != current_user.id:
        raise PermissionDeniedError("You don't own this workspace")

    update_data = data.model_dump(exclude_unset=True)
    if update_data:
        workspace = await workspace_repo.update(db, workspace_id, update_data)

    return {
        "success": True,
        "data": WorkspaceResponse.model_validate(workspace),
        "message": "Workspace updated",
    }


@router.delete("/{workspace_id}", response_model=ApiResponse)
async def delete_workspace(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a workspace and all its contents."""
    workspace = await workspace_repo.get_or_404(db, workspace_id)
    if workspace.owner_id != current_user.id:
        raise PermissionDeniedError("You don't own this workspace")

    await workspace_repo.delete(db, workspace_id)
    return {
        "success": True,
        "data": None,
        "message": "Workspace deleted",
    }