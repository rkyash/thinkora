"""Note repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.repositories.base import GenericRepo


class NoteRepo(GenericRepo[Note]):
    model = Note

    async def list_by_notebook(
        self, db: AsyncSession, notebook_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[Note]:
        """List notes in a notebook."""
        result = await db.execute(
            select(Note)
            .where(Note.notebook_id == notebook_id)
            .order_by(Note.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
