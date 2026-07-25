"""
Quiz and QuizQuestion models — AI-generated assessment quizzes.
QuizQuestion is included here as a tightly-coupled child entity (DEC-003).
"""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import QuestionType
from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    notebook_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    notebook: Mapped["Notebook"] = relationship(back_populates="quizzes")  # noqa: F821
    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Quiz {self.title or self.id}>"


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    quiz_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"), nullable=False
    )
    # [{text, is_correct}] for MCQ
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    quiz: Mapped["Quiz"] = relationship(back_populates="questions")

    def __repr__(self) -> str:
        return f"<QuizQuestion {self.type.value}: {self.question[:50]}>"
