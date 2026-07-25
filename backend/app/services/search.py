"""
Hybrid Search Service — combines semantic (Qdrant) and full-text (PostgreSQL)
search using Reciprocal Rank Fusion (RRF).

Architecture:
  1. Embed query via services/embedding.py (same model used for ingestion).
  2. Semantic search: Qdrant vector search across target notebook(s).
  3. Full-text search: PostgreSQL tsvector/tsquery on document_chunks.content.
  4. Merge: Reciprocal Rank Fusion → final ranked list.
  5. Enrich with source metadata (source name, notebook id).
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.chunk import DocumentChunk
from app.models.source import Source
from app.repositories.source import SourceRepo
from app.services.vector_store import get_vector_store

log: structlog.BoundLogger = structlog.get_logger(__name__)

source_repo = SourceRepo()

# Reciprocal Rank Fusion constant (standard value = 60)
RRF_K = 60


class SearchService:
    """
    Hybrid search combining Qdrant semantic search and PostgreSQL full-text.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._vector_store = get_vector_store()

    async def search(
        self,
        query: str,
        notebook_id: str | None = None,
        user_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
        semantic_top_k: int = 30,
        fts_top_k: int = 30,
    ) -> dict[str, Any]:
        """
        Perform hybrid search and return ranked results.

        Args:
            query: The user search query.
            notebook_id: Limit search to a specific notebook (optional).
            user_id: Limit search to notebooks owned by this user (optional).
            offset: Pagination offset.
            limit: Number of results to return.
            semantic_top_k: How many results to fetch from Qdrant.
            fts_top_k: How many results to fetch from Postgres FTS.

        Returns a dict with: query, results, total, offset, limit, has_next.
        """
        if not query.strip():
            return {
                "query": query,
                "results": [],
                "total": 0,
                "offset": offset,
                "limit": limit,
                "has_next": False,
            }

        # Run both search paths concurrently
        semantic_task = asyncio.create_task(
            self._semantic_search(query, notebook_id, semantic_top_k)
        )
        fts_task = asyncio.create_task(self._full_text_search(query, notebook_id, fts_top_k))

        semantic_results, fts_results = await asyncio.gather(
            semantic_task, fts_task, return_exceptions=True
        )

        # Handle individual failures gracefully
        if isinstance(semantic_results, Exception):
            log.warning("semantic_search_failed", error=str(semantic_results))
            semantic_results = []
        if isinstance(fts_results, Exception):
            log.warning("fts_search_failed", error=str(fts_results))
            fts_results = []

        # Merge via RRF
        merged = _rrf_merge(
            semantic_results,  # type: ignore[arg-type]
            fts_results,  # type: ignore[arg-type]
        )

        # Enrich with source metadata
        enriched = await self._enrich(merged)

        # Apply pagination
        total = len(enriched)
        page_items = enriched[offset : offset + limit]

        return {
            "query": query,
            "results": page_items,
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_next": (offset + limit) < total,
        }

    async def _semantic_search(
        self, query: str, notebook_id: str | None, top_k: int
    ) -> list[dict[str, Any]]:
        """Embed query and search Qdrant. Returns [{qdrant_id, score}]."""
        from app.services.embedding import get_embedding_service

        embed_svc = get_embedding_service()
        query_vector = await asyncio.to_thread(embed_svc.embed_query, query)

        if notebook_id:
            results = await self._vector_store.search(notebook_id, query_vector, limit=top_k)
        else:
            # No notebook filter — can't do cross-collection search in Qdrant easily,
            # fall back to empty (FTS will cover cross-notebook queries)
            results = []

        return [{"qdrant_id": r["id"], "score": r["score"]} for r in results]

    async def _full_text_search(
        self, query: str, notebook_id: str | None, top_k: int
    ) -> list[dict[str, Any]]:
        """
        PostgreSQL full-text search on document_chunks.content.
        Returns [{chunk_id, score}].
        """
        # Build tsquery — plainto_tsquery is safe against injection
        stmt = (
            select(
                DocumentChunk.id,
                func.ts_rank_cd(
                    func.to_tsvector("english", DocumentChunk.content),
                    func.plainto_tsquery("english", query),
                ).label("rank"),
            )
            .where(
                func.to_tsvector("english", DocumentChunk.content).op("@@")(
                    func.plainto_tsquery("english", query)
                )
            )
            .order_by(text("rank DESC"))
            .limit(top_k)
        )

        if notebook_id:
            stmt = stmt.where(DocumentChunk.notebook_id == notebook_id)

        result = await self._db.execute(stmt)
        rows = result.all()
        return [{"chunk_id": str(row.id), "score": float(row.rank)} for row in rows]

    async def _enrich(self, merged: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Fetch chunk + source metadata for each merged result.
        Skips results that can't be resolved (e.g. deleted chunks).
        """
        if not merged:
            return []

        # Collect qdrant_ids and chunk_ids
        qdrant_ids = [r["qdrant_id"] for r in merged if r.get("qdrant_id")]
        chunk_ids = [r["chunk_id"] for r in merged if r.get("chunk_id")]

        # Fetch chunks by qdrant_point_id
        chunk_map_by_qdrant: dict[str, DocumentChunk] = {}
        if qdrant_ids:
            from app.repositories.chunk import ChunkRepo

            cr = ChunkRepo()
            chunks = await cr.get_by_qdrant_ids(self._db, qdrant_ids)
            chunk_map_by_qdrant = {str(c.qdrant_point_id): c for c in chunks}

        # Fetch chunks by id
        chunk_map_by_id: dict[str, DocumentChunk] = {}
        if chunk_ids:
            result = await self._db.execute(
                select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
            )
            for c in result.scalars().all():
                chunk_map_by_id[str(c.id)] = c

        # Fetch sources
        all_source_ids: set[str] = set()
        for chunk in list(chunk_map_by_qdrant.values()) + list(chunk_map_by_id.values()):
            all_source_ids.add(str(chunk.source_id))

        source_map: dict[str, Source] = {}
        for sid in all_source_ids:
            src = await source_repo.get(self._db, sid)
            if src:
                source_map[sid] = src

        enriched: list[dict[str, Any]] = []
        for item in merged:
            chunk: DocumentChunk | None = None
            if item.get("qdrant_id"):
                chunk = chunk_map_by_qdrant.get(item["qdrant_id"])
            elif item.get("chunk_id"):
                chunk = chunk_map_by_id.get(item["chunk_id"])

            if chunk is None:
                continue

            source = source_map.get(str(chunk.source_id))
            enriched.append(
                {
                    "chunk_id": str(chunk.id),
                    "source_id": str(chunk.source_id),
                    "notebook_id": str(chunk.notebook_id),
                    "source_name": source.name if source else "",
                    "content": chunk.content or "",
                    "score": item["rrf_score"],
                    "rank_method": "rrf",
                }
            )

        return enriched


# ─── RRF helper ───────────────────────────────────────────────────────────────


def _rrf_merge(
    semantic: list[dict[str, Any]],
    fts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Reciprocal Rank Fusion — merges two ranked lists.

    Each item in semantic has: qdrant_id, score.
    Each item in fts has: chunk_id, score.
    The merged list has: qdrant_id?, chunk_id?, rrf_score.
    """
    scores: dict[str, dict[str, Any]] = {}

    for rank, item in enumerate(semantic, start=1):
        key = f"q:{item['qdrant_id']}"
        rrf = 1.0 / (RRF_K + rank)
        if key not in scores:
            scores[key] = {"qdrant_id": item["qdrant_id"], "rrf_score": 0.0}
        scores[key]["rrf_score"] += rrf

    for rank, item in enumerate(fts, start=1):
        key = f"c:{item['chunk_id']}"
        rrf = 1.0 / (RRF_K + rank)
        if key not in scores:
            scores[key] = {"chunk_id": item["chunk_id"], "rrf_score": 0.0}
        scores[key]["rrf_score"] += rrf

    return sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)
