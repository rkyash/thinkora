"""
ChatSession model — conversation container within a notebook.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.message import ChatMessage
    from app.models.notebook import Notebook


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    notebook_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    notebook: Mapped[Notebook] = relationship(back_populates="chat_sessions")  # noqa: F821
    messages: Mapped[list[ChatMessage]] = relationship(  # noqa: F821
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at"
    )

    def __repr__(self) -> str:
        return f"<ChatSession {self.title or self.id}>"
