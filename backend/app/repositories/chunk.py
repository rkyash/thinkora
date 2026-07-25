"""DocumentChunk repository — optimized for batch operations."""

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk
from app.repositories.base import GenericRepo


class ChunkRepo(GenericRepo[DocumentChunk]):
    model = DocumentChunk

    async def list_by_source(self, db: AsyncSession, source_id: str) -> list[DocumentChunk]:
        """Get all chunks for a source, ordered by index."""
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.source_id == source_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def delete_by_source(self, db: AsyncSession, source_id: str) -> int:
        """Delete all chunks for a source. Returns count deleted."""
        result = await db.execute(delete(DocumentChunk).where(DocumentChunk.source_id == source_id))
        await db.flush()
        return result.rowcount  # type: ignore[return-value]

    async def get_by_qdrant_ids(
        self, db: AsyncSession, qdrant_ids: list[str]
    ) -> list[DocumentChunk]:
        """Get chunks by their Qdrant point IDs."""
        if not qdrant_ids:
            return []
        result = await db.execute(
            select(DocumentChunk).where(DocumentChunk.qdrant_point_id.in_(qdrant_ids))
        )
        return list(result.scalars().all())
