"""
Knowledge Graph API — /api/v1/notebooks/{notebook_id}/graph

Endpoints:
  GET    /              Get full graph {nodes, edges}
  POST   /refresh       Regenerate graph via LLM pipeline
  POST   /nodes         Manually add a node
  DELETE /nodes/{id}    Delete a node + connected edges
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.models.user import User
from app.repositories import notebook_repo, workspace_repo
from app.schemas.graph import (
    GraphEdgeResponse,
    GraphNodeCreate,
    GraphNodeResponse,
    GraphRefreshRequest,
    GraphRefreshResponse,
    GraphResponse,
)
from app.schemas.response import ApiResponse, ok
from app.services.graph import GraphService

router = APIRouter(tags=["Knowledge Graph"])


# ─── Helpers ─────────────────────────────────────────────────────────────────


async def _verify_notebook_access(notebook_id: str, db: AsyncSession, user: User):
    notebook = await notebook_repo.get_or_404(db, notebook_id)
    workspace = await workspace_repo.get_or_404(db, str(notebook.workspace_id))
    if workspace.owner_id != user.id:
        raise PermissionDeniedError("You don't own this notebook")
    return notebook


# ─── Endpoints ───────────────────────────────────────────────────────────────


@router.get(
    "/notebooks/{notebook_id}/graph",
    response_model=ApiResponse[GraphResponse],
)
async def get_graph(
    notebook_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current knowledge graph (nodes + edges) for a notebook."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    svc = GraphService(db)
    graph = await svc.get_graph(str(notebook_id))
    return ok(
        GraphResponse(
            nodes=[GraphNodeResponse.model_validate(n) for n in graph["nodes"]],
            edges=[GraphEdgeResponse.model_validate(e) for e in graph["edges"]],
        )
    )


@router.post(
    "/notebooks/{notebook_id}/graph/refresh",
    response_model=ApiResponse[GraphResponse],
)
async def refresh_graph(
    notebook_id: UUID,
    payload: GraphRefreshRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Regenerate the knowledge graph using the LLM extraction pipeline.
    Runs synchronously (may take 10-30s depending on notebook size).
    For large notebooks, consider moving this to a Celery task.
    """
    await _verify_notebook_access(str(notebook_id), db, current_user)
    svc = GraphService(db)
    graph = await svc.refresh_graph(
        notebook_id=str(notebook_id),
        model=payload.model if payload else None,
    )
    return ok(
        GraphResponse(
            nodes=[GraphNodeResponse.model_validate(n) for n in graph["nodes"]],
            edges=[GraphEdgeResponse.model_validate(e) for e in graph["edges"]],
        ),
        "Graph regenerated successfully",
    )


@router.post(
    "/notebooks/{notebook_id}/graph/nodes",
    response_model=ApiResponse[GraphNodeResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_graph_node(
    notebook_id: UUID,
    payload: GraphNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually add a node to the knowledge graph."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    svc = GraphService(db)
    node = await svc.add_node(
        notebook_id=str(notebook_id),
        label=payload.label,
        node_type=payload.type,
        x_pos=payload.x_pos,
        y_pos=payload.y_pos,
    )
    return ok(GraphNodeResponse.model_validate(node), "Node added")


@router.delete(
    "/notebooks/{notebook_id}/graph/nodes/{node_id}",
    response_model=ApiResponse[None],
)
async def delete_graph_node(
    notebook_id: UUID,
    node_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a graph node and all edges connected to it."""
    await _verify_notebook_access(str(notebook_id), db, current_user)
    svc = GraphService(db)
    deleted = await svc.delete_node(node_id, str(notebook_id))
    if not deleted:
        raise NotFoundError("GraphNode", node_id)
    return ok(None, "Node deleted")
