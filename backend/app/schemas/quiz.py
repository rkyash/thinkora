"""
Pydantic v2 schemas for Quizzes and QuizQuestions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.constants import QuestionType

# ─── Request schemas ─────────────────────────────────────────────────────────


class QuizGenerateRequest(BaseModel):
    """Request body for AI quiz generation."""
    title: str | None = None
    question_count: int = 10
    question_types: list[QuestionType] = [QuestionType.MCQ, QuestionType.TRUE_FALSE]
    topic: str | None = None      # optional topic focus
    model: str | None = None      # override default LLM


# ─── Response schemas ─────────────────────────────────────────────────────────


class QuizQuestionResponse(BaseModel):
    """Single quiz question response."""
    id: str
    quiz_id: str
    question: str
    type: QuestionType
    options: Any | None           # [{text, is_correct}] for MCQ
    correct_answer: str | None
    explanation: str | None

    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    """Quiz without questions — used in list endpoints."""
    id: str
    notebook_id: str
    title: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizDetailResponse(BaseModel):
    """Quiz with all questions — used in detail endpoint."""
    id: str
    notebook_id: str
    title: str | None
    created_at: datetime
    questions: list[QuizQuestionResponse]

    model_config = {"from_attributes": True}
