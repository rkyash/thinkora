"""
Study Tools Service — AI-powered generation of flashcards, quizzes, summaries,
and study guides from notebook content.

Architecture:
  - Always routes LLM calls through services/llm.py (LiteLLM).
  - Reads source text directly from the DB (document_chunks table).
  - Persists generated items (Flashcard, Quiz, QuizQuestion) via repositories.
  - Returns raw Pydantic models; routers handle serialization.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Difficulty, GenerationType, QuestionType, TaskStatus
from app.core.logging import logger
from app.core.prompt_security import safe_user_block, sanitize_user_content
from app.models.flashcard import Flashcard
from app.models.generation import Generation
from app.models.quiz import Quiz, QuizQuestion
from app.repositories import (
    chunk_repo,
    flashcard_repo,
    generation_repo,
    quiz_repo,
    source_repo,
)
from app.services.llm import get_llm_service

log: structlog.BoundLogger = structlog.get_logger(__name__)

# ─── Prompt templates ────────────────────────────────────────────────────────

_FLASHCARD_PROMPT = """\
You are an expert study-card author. Generate exactly {count} high-quality flashcards \
from the source material below.

{difficulty_instruction}
{topic_instruction}

Output ONLY a valid JSON array — no markdown fences, no explanation:
[
  {{"question": "...", "answer": "...", "difficulty": "easy|medium|hard"}},
  ...
]

Rules:
- Questions must be specific and test real understanding, not trivia.
- Answers must be concise (1–3 sentences).
- Difficulty: easy = recall, medium = understanding, hard = application/analysis.
- If the material is short, generate as many good cards as possible (up to {count}).

Source material:
{content}
"""

_QUIZ_PROMPT = """\
You are an expert quiz author. Generate exactly {count} quiz questions from the source material below.

Question types to use (mix proportionally): {types}
{topic_instruction}

Output ONLY a valid JSON array — no markdown fences, no explanation:
[
  {{
    "question": "...",
    "type": "mcq|true_false|fill_blank|short_answer",
    "options": [{{"text": "...", "is_correct": true|false}}, ...],  // only for mcq
    "correct_answer": "...",   // text answer (T/F: "True" or "False")
    "explanation": "..."       // why this answer is correct
  }},
  ...
]

Rules:
- MCQ: exactly 4 options, exactly 1 correct.
- true_false: options field may be omitted, correct_answer = "True" or "False".
- fill_blank: question contains a blank (___), correct_answer = the missing word/phrase.
- short_answer: open-ended, correct_answer = a model answer (2–4 sentences).
- All questions must be answerable from the source material.

Source material:
{content}
"""

_SUMMARIZE_NOTE_PROMPT = """\
You are an expert academic summarizer. Summarize the following note content concisely \
and clearly. Preserve the key ideas, important terms, and any structure.

Output the summary in plain prose (2–5 sentences for short notes, a few paragraphs for \
longer ones). Do NOT use bullet points unless the original is structured as a list.

Note content:
{content}
"""

_SUMMARY_GENERATION_PROMPT = """\
You are an expert academic summarizer. Summarize the key ideas from all the source \
material in this notebook. Organize by theme if the sources cover multiple topics.

Output a well-structured summary in markdown format with:
- An executive overview (2–3 sentences)
- Key Concepts section with brief explanations
- Important Details worth remembering
- A "Further Questions" section with 3–5 open questions for deeper study

Source material:
{content}
"""

_STUDY_GUIDE_PROMPT = """\
You are an expert educator. Create a comprehensive study guide from the source material below.

Output in markdown format:
# Study Guide: {notebook_name}

## Learning Objectives
(3–5 clear objectives)

## Core Concepts
(Each concept: definition + example + why it matters)

## Key Terms & Definitions
(Glossary of important terms)

## Important Connections
(How concepts relate to each other)

## Practice Questions
(5 thought-provoking questions to test understanding)

## Summary
(Brief wrap-up paragraph)

Source material:
{content}
"""


# ─── Helper functions ─────────────────────────────────────────────────────────


def _extract_json(text: str) -> Any:
    """Extract and parse the first JSON array or object from LLM output."""
    # Strip markdown code fences if present
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.strip().rstrip("`").strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array/object inside text
    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from LLM output: {text[:200]}")


async def _collect_notebook_text(db: AsyncSession, notebook_id: str, max_chars: int = 60_000) -> str:
    """Aggregate document chunk text from a notebook (up to max_chars)."""
    chunks = await chunk_repo.list_all(db, notebook_id=notebook_id, limit=500)
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        if total >= max_chars:
            break
        text = chunk.content or ""
        parts.append(text)
        total += len(text)
    raw = "\n\n".join(parts)
    # Sanitize aggregated source text before embedding in prompts (TASK-207)
    return sanitize_user_content(raw, max_chars=max_chars)


# ─── StudyToolsService ───────────────────────────────────────────────────────


class StudyToolsService:
    """
    AI-powered study tools generator for Thinkora.

    All LLM calls are routed through get_llm_service() — never call provider
    SDKs (OpenAI, Anthropic, etc.) directly from this service.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._llm = get_llm_service()

    # ─── Notes summarization ─────────────────────────────────────────────

    async def summarize_note(
        self,
        note_id: str,
        content: str,
        model: str | None = None,
    ) -> str:
        """
        Summarize the content of a note using the LLM.
        Returns the summary string; caller is responsible for storing it.
        """
        if not content or not content.strip():
            return "No content to summarize."

        safe_content = sanitize_user_content(content, max_chars=20_000)
        prompt = _SUMMARIZE_NOTE_PROMPT.format(content=safe_content)
        messages = [{"role": "user", "content": prompt}]

        log.info("summarize_note_start", note_id=note_id)
        summary = await self._llm.get_chat_completion(messages=messages, model=model, temperature=0.3)
        log.info("summarize_note_done", note_id=note_id, summary_len=len(summary))
        return summary

    # ─── Flashcard generation ─────────────────────────────────────────────

    async def generate_flashcards(
        self,
        notebook_id: str,
        count: int = 10,
        difficulty: Difficulty | None = None,
        topic: str | None = None,
        model: str | None = None,
    ) -> list[Flashcard]:
        """
        Generate AI flashcards for a notebook and persist them to the DB.
        Returns the list of created Flashcard ORM objects.
        """
        content = await _collect_notebook_text(self._db, notebook_id)
        if not content.strip():
            raise ValueError("No source content found in notebook to generate flashcards.")

        difficulty_instruction = (
            f"Focus on {difficulty.value} difficulty cards."
            if difficulty
            else "Generate a mix of easy, medium, and hard difficulty cards."
        )
        topic_instruction = f"Focus specifically on the topic: {topic}." if topic else ""

        prompt = _FLASHCARD_PROMPT.format(
            count=count,
            difficulty_instruction=difficulty_instruction,
            topic_instruction=topic_instruction,
            content=content[:50_000],
        )
        messages = [{"role": "user", "content": prompt}]

        log.info("generate_flashcards_start", notebook_id=notebook_id, count=count)
        raw = await self._llm.get_chat_completion(messages=messages, model=model, temperature=0.6)

        try:
            cards_data = _extract_json(raw)
        except ValueError as exc:
            log.error("flashcard_json_parse_error", error=str(exc), notebook_id=notebook_id)
            raise

        if not isinstance(cards_data, list):
            raise ValueError("LLM returned non-list JSON for flashcards")

        # Validate & create cards
        rows: list[dict] = []
        for item in cards_data:
            if not isinstance(item, dict):
                continue
            raw_diff = item.get("difficulty", "medium").lower()
            try:
                diff = Difficulty(raw_diff)
            except ValueError:
                diff = Difficulty.MEDIUM

            rows.append(
                {
                    "notebook_id": notebook_id,
                    "question": str(item.get("question", "")).strip(),
                    "answer": str(item.get("answer", "")).strip(),
                    "difficulty": diff,
                }
            )

        if not rows:
            raise ValueError("LLM generated zero valid flashcards")

        cards = await flashcard_repo.bulk_create(self._db, rows)
        log.info("generate_flashcards_done", notebook_id=notebook_id, count=len(cards))
        return cards

    # ─── Quiz generation ─────────────────────────────────────────────────

    async def generate_quiz(
        self,
        notebook_id: str,
        title: str | None = None,
        question_count: int = 10,
        question_types: list[QuestionType] | None = None,
        topic: str | None = None,
        model: str | None = None,
    ) -> Quiz:
        """
        Generate an AI quiz (with questions) for a notebook and persist it.
        Returns the Quiz ORM object (questions loaded).
        """
        if question_types is None:
            question_types = [QuestionType.MCQ, QuestionType.TRUE_FALSE]

        content = await _collect_notebook_text(self._db, notebook_id)
        if not content.strip():
            raise ValueError("No source content found in notebook to generate a quiz.")

        types_str = ", ".join(t.value for t in question_types)
        topic_instruction = f"Focus specifically on the topic: {topic}." if topic else ""

        prompt = _QUIZ_PROMPT.format(
            count=question_count,
            types=types_str,
            topic_instruction=topic_instruction,
            content=content[:50_000],
        )
        messages = [{"role": "user", "content": prompt}]

        log.info("generate_quiz_start", notebook_id=notebook_id, count=question_count)
        raw = await self._llm.get_chat_completion(messages=messages, model=model, temperature=0.5)

        try:
            questions_data = _extract_json(raw)
        except ValueError as exc:
            log.error("quiz_json_parse_error", error=str(exc), notebook_id=notebook_id)
            raise

        if not isinstance(questions_data, list):
            raise ValueError("LLM returned non-list JSON for quiz questions")

        # Create Quiz
        quiz_title = title or "AI-Generated Quiz"
        quiz = await quiz_repo.create(
            self._db, {"notebook_id": notebook_id, "title": quiz_title}
        )

        # Create questions
        question_rows: list[dict] = []
        for item in questions_data:
            if not isinstance(item, dict):
                continue
            raw_type = item.get("type", "mcq").lower()
            try:
                q_type = QuestionType(raw_type)
            except ValueError:
                q_type = QuestionType.MCQ

            question_rows.append(
                {
                    "quiz_id": str(quiz.id),
                    "question": str(item.get("question", "")).strip(),
                    "type": q_type,
                    "options": item.get("options"),
                    "correct_answer": item.get("correct_answer"),
                    "explanation": item.get("explanation"),
                }
            )

        from app.models.quiz import QuizQuestion as QuizQuestionModel
        from app.repositories.base import GenericRepo

        class _QuizQuestionRepo(GenericRepo[QuizQuestionModel]):
            model = QuizQuestionModel

        qq_repo = _QuizQuestionRepo()
        if question_rows:
            await qq_repo.bulk_create(self._db, question_rows)

        # Reload quiz with questions eagerly
        quiz = await quiz_repo.get_with_questions(self._db, str(quiz.id))  # type: ignore[assignment]
        log.info("generate_quiz_done", notebook_id=notebook_id, quiz_id=str(quiz.id))
        return quiz

    # ─── Summary generation ──────────────────────────────────────────────

    async def generate_summary(
        self,
        notebook_id: str,
        model: str | None = None,
    ) -> Generation:
        """
        Generate a markdown summary of all sources in a notebook.
        Persists a Generation record (type=summary) and returns it.
        """
        content = await _collect_notebook_text(self._db, notebook_id)
        if not content.strip():
            raise ValueError("No source content found in notebook to summarize.")

        # content is already sanitized by _collect_notebook_text()
        prompt = _SUMMARY_GENERATION_PROMPT.format(content=content)
        messages = [{"role": "user", "content": prompt}]

        log.info("generate_summary_start", notebook_id=notebook_id)
        summary_text = await self._llm.get_chat_completion(
            messages=messages, model=model, temperature=0.4
        )

        generation = await generation_repo.create(
            self._db,
            {
                "notebook_id": notebook_id,
                "type": GenerationType.SUMMARY,
                "status": TaskStatus.READY,
                "content": {"text": summary_text},
            },
        )
        log.info("generate_summary_done", notebook_id=notebook_id, gen_id=str(generation.id))
        return generation

    # ─── Study guide generation ─────────────────────────────────────────

    async def generate_study_guide(
        self,
        notebook_id: str,
        notebook_name: str = "Notebook",
        model: str | None = None,
    ) -> Generation:
        """
        Generate a full structured study guide markdown document.
        Persists a Generation record (type=study_guide) and returns it.
        """
        content = await _collect_notebook_text(self._db, notebook_id)
        if not content.strip():
            raise ValueError("No source content found in notebook for study guide.")

        # content is already sanitized by _collect_notebook_text()
        # Also sanitize notebook_name to prevent injection through user-named notebooks
        safe_name = sanitize_user_content(notebook_name, max_chars=200)
        prompt = _STUDY_GUIDE_PROMPT.format(
            notebook_name=safe_name, content=content
        )
        messages = [{"role": "user", "content": prompt}]

        log.info("generate_study_guide_start", notebook_id=notebook_id)
        guide_text = await self._llm.get_chat_completion(
            messages=messages, model=model, temperature=0.4
        )

        generation = await generation_repo.create(
            self._db,
            {
                "notebook_id": notebook_id,
                "type": GenerationType.STUDY_GUIDE,
                "status": TaskStatus.READY,
                "content": {"text": guide_text},
            },
        )
        log.info("generate_study_guide_done", notebook_id=notebook_id, gen_id=str(generation.id))
        return generation
