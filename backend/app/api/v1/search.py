"""
Search API — /api/v1/search

Endpoints:
  GET    /     Hybrid semantic + full-text search across notebook(s)
               Query params: q, notebook_id (optional), offset, limit
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.response import ok
from app.schemas.search import SearchResponse, SearchResultItem
from app.services.search import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/", response_model=SearchResponse)
async def hybrid_search(
    q: str = Query(..., min_length=1, description="Search query"),
    notebook_id: str | None = Query(None, description="Limit search to a specific notebook"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Hybrid search combining semantic (Qdrant) + full-text (PostgreSQL) search.
    Results are ranked using Reciprocal Rank Fusion (RRF).
    Optionally filter by notebook_id.
    """
    svc = SearchService(db)
    result = await svc.search(
        query=q,
        notebook_id=notebook_id,
        user_id=current_user.id,
        offset=offset,
        limit=limit,
    )
    return SearchResponse(
        query=result["query"],
        results=[SearchResultItem(**item) for item in result["results"]],
        total=result["total"],
        offset=result["offset"],
        limit=result["limit"],
        has_next=result["has_next"],
    )
