"""
DocumentChunk model — chunked text with Qdrant vector reference.
"""

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    source_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    # Denormalized for query performance (avoid JOIN through sources)
    notebook_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("notebooks.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qdrant_point_id: Mapped[str | None] = mapped_column(PG_UUID(as_uuid=False), nullable=True)

    # Relationships
    source: Mapped["Source"] = relationship(back_populates="chunks")  # noqa: F821

    def __repr__(self) -> str:
        return f"<DocumentChunk {self.source_id}[{self.chunk_index}]>"
