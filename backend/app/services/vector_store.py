"""
Vector store service — Qdrant abstraction layer.

Uses the synchronous ``qdrant_client.QdrantClient`` and wraps blocking calls
with ``asyncio.to_thread`` so the service fits naturally into async FastAPI
handlers and Celery workers.

Usage:
    from app.services.vector_store import get_vector_store

    store = get_vector_store()
    await store.ensure_collection(notebook_id)
    await store.upsert(notebook_id, points)
    results = await store.search(notebook_id, query_vector, limit=5)
"""

from __future__ import annotations

import asyncio
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

from app.config import settings
from app.core.constants import EMBEDDING_DIMENSIONS
from app.core.logging import logger

# ─── Constants ────────────────────────────────────────────────────────

COLLECTION_PREFIX = "thinkora_"


def _collection_name(notebook_id: str) -> str:
    """Build the Qdrant collection name for a notebook."""
    return f"{COLLECTION_PREFIX}{notebook_id}"


# ─── Service ──────────────────────────────────────────────────────────


class VectorStoreService:
    """Async-friendly wrapper around the Qdrant sync client.

    All heavy I/O is offloaded to a thread via ``asyncio.to_thread`` so the
    event loop is never blocked.
    """

    def __init__(
        self,
        host: str = settings.QDRANT_HOST,
        port: int = settings.QDRANT_PORT,
        api_key: str = settings.QDRANT_API_KEY,
    ) -> None:
        client_kwargs: dict[str, Any] = {
            "host": host,
            "port": port,
            "timeout": 30,
        }
        if api_key:
            client_kwargs["api_key"] = api_key

        self._client = QdrantClient(**client_kwargs)

        logger.info(
            "vector_store_initialized",
            host=host,
            port=port,
            has_api_key=bool(api_key),
        )

    # ── Collection management ─────────────────────────────────

    async def ensure_collection(self, notebook_id: str) -> None:
        """Create the Qdrant collection if it does not already exist.

        Uses cosine distance and the configured ``EMBEDDING_DIMENSIONS``.
        """
        name = _collection_name(notebook_id)

        def _create() -> None:
            existing = {c.name for c in self._client.get_collections().collections}
            if name in existing:
                logger.debug("collection_exists", collection=name)
                return

            self._client.create_collection(
                collection_name=name,
                vectors_config=qmodels.VectorParams(
                    size=EMBEDDING_DIMENSIONS,
                    distance=qmodels.Distance.COSINE,
                ),
            )
            logger.info(
                "collection_created",
                collection=name,
                dimensions=EMBEDDING_DIMENSIONS,
            )

        await asyncio.to_thread(_create)

    async def delete_collection(self, notebook_id: str) -> None:
        """Drop the entire collection for a notebook."""
        name = _collection_name(notebook_id)

        def _delete() -> None:
            try:
                self._client.delete_collection(collection_name=name)
                logger.info("collection_deleted", collection=name)
            except Exception:
                # Collection may not exist — idempotent delete
                logger.debug("collection_delete_noop", collection=name)

        await asyncio.to_thread(_delete)

    # ── Point operations ──────────────────────────────────────

    async def upsert(self, notebook_id: str, points: list[dict[str, Any]]) -> None:
        """Upsert embedding points into the notebook's collection.

        Each dict in *points* must contain:
          - ``id``: str (UUID or integer point ID)
          - ``vector``: list[float]
          - ``payload``: dict
        """
        if not points:
            return

        name = _collection_name(notebook_id)

        qdrant_points = [
            qmodels.PointStruct(
                id=p["id"],
                vector=p["vector"],
                payload=p.get("payload", {}),
            )
            for p in points
        ]

        def _upsert() -> None:
            self._client.upsert(
                collection_name=name,
                points=qdrant_points,
            )

        await asyncio.to_thread(_upsert)

        logger.info(
            "vectors_upserted",
            collection=name,
            count=len(qdrant_points),
        )

    async def search(
        self,
        notebook_id: str,
        query_vector: list[float],
        *,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search for nearest neighbours in the notebook's collection.

        Args:
            notebook_id: Which notebook collection to search.
            query_vector: The query embedding vector.
            limit: Maximum number of results to return.

        Returns:
            List of dicts with ``id``, ``score``, and ``payload`` keys.
        """
        name = _collection_name(notebook_id)

        def _search() -> list[qmodels.ScoredPoint]:
            response = self._client.query_points(
                collection_name=name,
                query=query_vector,
                limit=limit,
                with_payload=True,
            )
            return response.points

        hits = await asyncio.to_thread(_search)

        results: list[dict[str, Any]] = [
            {
                "id": str(hit.id),
                "score": hit.score,
                "payload": hit.payload or {},
            }
            for hit in hits
        ]

        logger.debug(
            "vector_search",
            collection=name,
            limit=limit,
            hits=len(results),
        )
        return results

    async def delete_by_source(self, notebook_id: str, source_id: str) -> None:
        """Delete all points belonging to a specific source from the collection.

        Uses a payload filter on the ``source_id`` field.
        """
        name = _collection_name(notebook_id)

        def _delete() -> None:
            self._client.delete(
                collection_name=name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="source_id",
                                match=qmodels.MatchValue(value=source_id),
                            ),
                        ],
                    ),
                ),
            )

        await asyncio.to_thread(_delete)

        logger.info(
            "vectors_deleted_by_source",
            collection=name,
            source_id=source_id,
        )


# ─── Singleton Factory ───────────────────────────────────────────────

_instance: VectorStoreService | None = None


def get_vector_store() -> VectorStoreService:
    """Return the module-level ``VectorStoreService`` singleton."""
    global _instance  # noqa: PLW0603

    if _instance is not None:
        return _instance

    _instance = VectorStoreService()
    return _instance


def reset_vector_store() -> None:
    """Reset the singleton (for testing)."""
    global _instance  # noqa: PLW0603
    _instance = None
