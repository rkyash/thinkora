"""
Pydantic v2 schemas for Knowledge Graph — nodes, edges, requests, responses.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.core.constants import GraphNodeType

# ─── Request schemas ─────────────────────────────────────────────────────────


class GraphNodeCreate(BaseModel):
    """Manually create a graph node."""
    label: str
    type: GraphNodeType = GraphNodeType.CONCEPT
    x_pos: float = 0.0
    y_pos: float = 0.0


class GraphRefreshRequest(BaseModel):
    """Request body for graph regeneration (optional model override)."""
    model: str | None = None


# ─── Response schemas ─────────────────────────────────────────────────────────


class GraphNodeResponse(BaseModel):
    """Single graph node."""
    id: str
    notebook_id: str
    label: str
    type: GraphNodeType
    x_pos: float | None
    y_pos: float | None

    model_config = {"from_attributes": True}


class GraphEdgeResponse(BaseModel):
    """Single graph edge."""
    id: str
    notebook_id: str
    source_node: str
    target_node: str
    label: str | None

    model_config = {"from_attributes": True}


class GraphResponse(BaseModel):
    """Full graph — nodes + edges."""
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]


class GraphRefreshResponse(BaseModel):
    """Response after dispatching graph refresh task."""
    task_id: str
    message: str = "Graph regeneration started"
