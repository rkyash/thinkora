"""
Sources API — CRUD endpoints for sources within notebooks.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.source import Source
from app.models.user import User
from app.repositories import chunk_repo, notebook_repo, source_repo, workspace_repo
from app.schemas.pagination import OffsetParams, get_offset_params
from app.schemas.response import ApiResponse, PaginatedResponse
from app.schemas.source import (
    SourceListResponse,
    SourceResponse,
    SourceTextRequest,
    SourceUrlRequest,
    SourceYoutubeRequest,
)
from app.services.storage import get_storage
from app.services.vector_store import get_vector_store
from app.workers.ingestion_tasks import ingest_source_task

router = APIRouter(prefix="/notebooks/{notebook_id}/sources", tags=["Sources"])


async def _verify_workspace_ownership(
    workspace_id: str, db: AsyncSession, current_user: User
) -> Any:
    """Verify the workspace exists and is owned by the current user."""
    workspace = await workspace_repo.get_or_404(db, workspace_id)
    if workspace.owner_id != current_user.id:
        raise PermissionDeniedError("You don't own this workspace")
    return workspace


async def _verify_notebook_access(
    workspace_id: str,
    notebook_id: str,
    db: AsyncSession,
    current_user: User,
) -> Any:
    """Verify workspace ownership and notebook access."""
    # Verify workspace ownership
    await _verify_workspace_ownership(workspace_id, db, current_user)

    # Verify notebook belongs to workspace
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    if notebook.workspace_id != workspace_id:
        raise NotFoundError("Notebook not found in this workspace")

    return notebook


@router.post(
    "/upload", response_model=ApiResponse[SourceResponse], status_code=status.HTTP_201_CREATED
)
async def upload_source(
    workspace_id: str,
    notebook_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a file as a source."""
    notebook = await _verify_notebook_access(workspace_id, notebook_id, db, current_user)

    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided",
        )

    # Read file content
    content = await file.read()

    # Store file
    storage = get_storage()
    file_path = f"{notebook.id}/{file.filename}"
    file_path = await storage.save(
        file_path,
        content,
    )

    # Create source record
    # Determine source type from file extension
    file_extension = Path(file.filename).suffix.lower()
    type_mapping = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".xlsx": "xlsx",
        ".csv": "csv",
        ".md": "markdown",
        ".markdown": "markdown",
        ".txt": "txt",
    }
    source_type = type_mapping.get(file_extension, "txt")

    source_data = {
        "notebook_id": notebook.id,
        "name": file.filename,
        "type": source_type,
        "file_path": file_path,
        "char_count": len(content) if source_type == "txt" else None,
        "status": "pending",
    }

    source = await source_repo.create(db, source_data)

    # Trigger ingestion process
    ingest_source_task.delay(str(source.id))

    return ApiResponse[SourceResponse](
        data=source, success=True, message="Source created successfully"
    )


@router.post(
    "/url", response_model=ApiResponse[SourceResponse], status_code=status.HTTP_201_CREATED
)
async def create_url_source(
    workspace_id: str,
    notebook_id: str,
    data: SourceUrlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a URL source."""
    notebook = await _verify_notebook_access(workspace_id, notebook_id, db, current_user)

    # Create source record
    source_data = {
        "notebook_id": notebook.id,
        "name": data.name,
        "type": "url",
        "url": str(data.url),
        "status": "pending",
    }

    source = await source_repo.create(db, source_data)

    # Trigger ingestion process
    ingest_source_task.delay(str(source.id))

    return ApiResponse[SourceResponse](
        data=source, success=True, message="Source created successfully"
    )


@router.post(
    "/youtube", response_model=ApiResponse[SourceResponse], status_code=status.HTTP_201_CREATED
)
async def create_youtube_source(
    workspace_id: str,
    notebook_id: str,
    data: SourceYoutubeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a YouTube source."""
    notebook = await _verify_notebook_access(workspace_id, notebook_id, db, current_user)

    # Create source record
    source_data = {
        "notebook_id": notebook.id,
        "name": data.name,
        "type": "youtube",
        "url": str(data.url),
        "status": "pending",
    }

    source = await source_repo.create(db, source_data)

    # Trigger ingestion process
    ingest_source_task.delay(str(source.id))

    return ApiResponse[SourceResponse](
        data=source, success=True, message="Source created successfully"
    )


@router.post(
    "/text", response_model=ApiResponse[SourceResponse], status_code=status.HTTP_201_CREATED
)
async def create_text_source(
    workspace_id: str,
    notebook_id: str,
    data: SourceTextRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a text source."""
    notebook = await _verify_notebook_access(workspace_id, notebook_id, db, current_user)

    # Store text content as a file
    storage = get_storage()
    filename = data.name or f"text-{uuid.uuid4().hex}.txt"
    file_path = f"{notebook.id}/{filename}"
    file_path = await storage.save(
        file_path,
        data.content.encode("utf-8"),
    )

    # Create source record
    source_data = {
        "notebook_id": notebook.id,
        "name": filename,
        "type": "text",
        "file_path": file_path,
        "char_count": len(data.content),
        "status": "pending",
    }

    source = await source_repo.create(db, source_data)

    # Trigger ingestion process
    ingest_source_task.delay(str(source.id))

    return ApiResponse[SourceResponse](
        data=source, success=True, message="Source created successfully"
    )


@router.get("/", response_model=PaginatedResponse[SourceListResponse])
async def list_sources(
    workspace_id: str,
    notebook_id: str,
    offset_params: OffsetParams = Depends(get_offset_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List sources in a notebook."""
    notebook = await _verify_notebook_access(workspace_id, notebook_id, db, current_user)

    sources = await source_repo.list_by_notebook(
        db, str(notebook.id), offset=offset_params.offset, limit=offset_params.limit
    )
    total = await source_repo.count(db, notebook_id=str(notebook.id))
    return {
        "success": True,
        "data": [SourceListResponse.model_validate(source) for source in sources],
        "total": total,
        "offset": offset_params.offset,
        "limit": offset_params.limit,
        "has_next": (offset_params.offset + offset_params.limit) < total,
    }


@router.get("/{source_id}", response_model=ApiResponse[SourceResponse])
async def get_source(
    workspace_id: str,
    notebook_id: str,
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific source."""
    notebook = await _verify_notebook_access(workspace_id, notebook_id, db, current_user)

    source = await source_repo.get_or_404(db, source_id)
    if str(source.notebook_id) != str(notebook.id):
        raise NotFoundError("Source not found in this notebook")

    return ApiResponse[SourceResponse](
        data=source, success=True, message="Source retrieved successfully"
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    workspace_id: str,
    notebook_id: str,
    source_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a source."""
    notebook = await _verify_notebook_access(workspace_id, notebook_id, db, current_user)

    source = await source_repo.get_or_404(db, source_id)
    if str(source.notebook_id) != str(notebook.id):
        raise NotFoundError("Source not found in this notebook")

    # Delete associated file if exists
    if source.file_path:
        storage = get_storage()
        await storage.delete(source.file_path)

    # Delete associated chunks
    await chunk_repo.delete_by_source(db, str(source.id))

    # Delete associated vectors from Qdrant
    vector_store = get_vector_store()
    await vector_store.delete_by_source(str(notebook.id), str(source.id))

    # Delete source record
    await source_repo.delete(db, source_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
