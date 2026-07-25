"""ChatSession repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_session import ChatSession
from app.repositories.base import GenericRepo


class ChatSessionRepo(GenericRepo[ChatSession]):
    model = ChatSession

    async def list_by_notebook(
        self, db: AsyncSession, notebook_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[ChatSession]:
        """List chat sessions in a notebook."""
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.notebook_id == notebook_id)
            .order_by(ChatSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
