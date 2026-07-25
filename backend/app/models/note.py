"""
Note model — TipTap rich-text notes with backlinks.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Note(Base):
    __tablename__ = "notes"

    notebook_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # TipTap JSON doc
    # [{note_id, title}]
    backlinks: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    notebook: Mapped["Notebook"] = relationship(back_populates="notes")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Note {self.title or self.id}>"
