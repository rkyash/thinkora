"""ChatMessage repository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import ChatMessage
from app.repositories.base import GenericRepo


class MessageRepo(GenericRepo[ChatMessage]):
    model = ChatMessage

    async def list_by_session(
        self, db: AsyncSession, session_id: str, *, offset: int = 0, limit: int = 50
    ) -> list[ChatMessage]:
        """List messages in a chat session, chronological order."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self, db: AsyncSession, session_id: str, k: int = 10
    ) -> list[ChatMessage]:
        """Get the most recent k messages for conversation history."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(k)
        )
        # Reverse to get chronological order
        messages = list(result.scalars().all())
        messages.reverse()
        return messages
