"""Quiz repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import Quiz, QuizQuestion
from app.repositories.base import GenericRepo


class QuizRepo(GenericRepo[Quiz]):
    model = Quiz

    async def list_by_notebook(
        self, db: AsyncSession, notebook_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[Quiz]:
        """List quizzes in a notebook."""
        result = await db.execute(
            select(Quiz)
            .where(Quiz.notebook_id == notebook_id)
            .order_by(Quiz.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_questions(self, db: AsyncSession, quiz_id: str) -> Quiz | None:
        """Get a quiz with all its questions eagerly loaded."""
        result = await db.execute(
            select(Quiz)
            .where(Quiz.id == quiz_id)
            .options(selectinload(Quiz.questions))
        )
        return result.scalar_one_or_none()
