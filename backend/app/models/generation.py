"""
Generation model — AI-generated content (summaries, quizzes, podcasts, etc.).
Includes `status` field missing from original spec (DEC-002).
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import GenerationType, TaskStatus
from app.database import Base


class Generation(Base):
    __tablename__ = "generations"

    notebook_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[GenerationType] = mapped_column(
        Enum(GenerationType, name="generation_type"), nullable=False
    )
    # Status field — added per DEC-002 (missing from original spec)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), default=TaskStatus.PENDING
    )
    content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # podcast type only
    task_id: Mapped[str | None] = mapped_column(Text, nullable=True)  # Celery task ID
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    notebook: Mapped["Notebook"] = relationship(back_populates="generations")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Generation {self.type.value} ({self.status.value})>"
