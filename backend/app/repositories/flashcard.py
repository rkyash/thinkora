"""Flashcard repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.flashcard import Flashcard
from app.repositories.base import GenericRepo


class FlashcardRepo(GenericRepo[Flashcard]):
    model = Flashcard

    async def list_by_notebook(
        self, db: AsyncSession, notebook_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[Flashcard]:
        """List flashcards in a notebook with pagination."""
        result = await db.execute(
            select(Flashcard)
            .where(Flashcard.notebook_id == notebook_id)
            .order_by(Flashcard.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
