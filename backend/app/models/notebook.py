"""
Notebook model — contains sources, chats, notes, study tools.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.chat_session import ChatSession
    from app.models.flashcard import Flashcard
    from app.models.generation import Generation
    from app.models.graph_edge import GraphEdge
    from app.models.graph_node import GraphNode
    from app.models.note import Note
    from app.models.quiz import Quiz
    from app.models.source import Source
    from app.models.workspace import Workspace


class Notebook(Base):
    __tablename__ = "notebooks"

    workspace_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    emoji: Mapped[str] = mapped_column(String(10), default="📓")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    workspace: Mapped[Workspace] = relationship(back_populates="notebooks")  # noqa: F821
    sources: Mapped[list[Source]] = relationship(  # noqa: F821
        back_populates="notebook", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list[ChatSession]] = relationship(  # noqa: F821
        back_populates="notebook", cascade="all, delete-orphan"
    )
    notes: Mapped[list[Note]] = relationship(  # noqa: F821
        back_populates="notebook", cascade="all, delete-orphan"
    )
    flashcards: Mapped[list[Flashcard]] = relationship(  # noqa: F821
        back_populates="notebook", cascade="all, delete-orphan"
    )
    quizzes: Mapped[list[Quiz]] = relationship(  # noqa: F821
        back_populates="notebook", cascade="all, delete-orphan"
    )
    graph_nodes: Mapped[list[GraphNode]] = relationship(  # noqa: F821
        back_populates="notebook", cascade="all, delete-orphan"
    )
    graph_edges: Mapped[list[GraphEdge]] = relationship(  # noqa: F821
        back_populates="notebook", cascade="all, delete-orphan"
    )
    generations: Mapped[list[Generation]] = relationship(  # noqa: F821
        back_populates="notebook", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Notebook {self.emoji} {self.name}>"
