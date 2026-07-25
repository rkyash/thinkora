"""
Pydantic v2 schemas for Hybrid Search results.
"""

from __future__ import annotations

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    """A single search result — a ranked document chunk with metadata."""
    chunk_id: str
    source_id: str
    notebook_id: str
    source_name: str
    content: str
    score: float
    rank_method: str = "rrf"   # reciprocal rank fusion


class SearchResponse(BaseModel):
    """Paginated hybrid search response."""
    query: str
    results: list[SearchResultItem]
    total: int
    offset: int
    limit: int
    has_next: bool
