"""Generation repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import GenerationType
from app.models.generation import Generation
from app.repositories.base import GenericRepo


class GenerationRepo(GenericRepo[Generation]):
    model = Generation

    async def list_by_notebook(
        self, db: AsyncSession, notebook_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[Generation]:
        """List all generations for a notebook."""
        result = await db.execute(
            select(Generation)
            .where(Generation.notebook_id == notebook_id)
            .order_by(Generation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_type(
        self,
        db: AsyncSession,
        notebook_id: str,
        gen_type: GenerationType,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Generation]:
        """List generations of a specific type for a notebook."""
        result = await db.execute(
            select(Generation)
            .where(
                Generation.notebook_id == notebook_id,
                Generation.type == gen_type,
            )
            .order_by(Generation.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
