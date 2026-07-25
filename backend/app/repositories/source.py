"""Source repository."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import SourceStatus
from app.models.source import Source
from app.repositories.base import GenericRepo


class SourceRepo(GenericRepo[Source]):
    model = Source

    async def list_by_notebook(
        self, db: AsyncSession, notebook_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[Source]:
        """List sources in a notebook."""
        result = await db.execute(
            select(Source)
            .where(Source.notebook_id == notebook_id)
            .order_by(Source.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        db: AsyncSession,
        source_id: str,
        status: SourceStatus,
        error_message: str | None = None,
        **kwargs: Any,
    ) -> Source:
        """Update source processing status."""
        data: dict[str, Any] = {"status": status}
        if error_message is not None:
            data["error_message"] = error_message
        data.update(kwargs)
        return await self.update(db, source_id, data)
