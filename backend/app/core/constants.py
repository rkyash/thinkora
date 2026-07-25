"""
Application-wide constants, enums, and magic strings.
"""

import enum


class SourceType(str, enum.Enum):
    """Supported source document types."""

    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    CSV = "csv"
    MARKDOWN = "markdown"
    TXT = "txt"
    PPTX = "pptx"
    EPUB = "epub"
    URL = "url"
    YOUTUBE = "youtube"
    AUDIO = "audio"
    IMAGE = "image"
    TEXT = "text"


class SourceStatus(str, enum.Enum):
    """Source processing status lifecycle."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class MessageRole(str, enum.Enum):
    """Chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"


class Difficulty(str, enum.Enum):
    """Flashcard difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, enum.Enum):
    """Quiz question types."""

    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"


class GraphNodeType(str, enum.Enum):
    """Knowledge graph node types."""

    CONCEPT = "concept"
    ENTITY = "entity"
    TOPIC = "topic"
    PERSON = "person"
    PLACE = "place"
    EVENT = "event"


class GenerationType(str, enum.Enum):
    """Content generation types."""

    SUMMARY = "summary"
    QUIZ = "quiz"
    FLASHCARDS = "flashcards"
    STUDY_GUIDE = "study_guide"
    PODCAST = "podcast"


class TaskStatus(str, enum.Enum):
    """Async task status (Celery tasks, generations)."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


# ─── Application Constants ───────────────────────────────────

APP_NAME = "Thinkora"
API_V1_PREFIX = "/api/v1"
DEFAULT_PAGE_LIMIT = 50
MAX_PAGE_LIMIT = 200

# Chunking defaults
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Conversation history window
CONVERSATION_HISTORY_K = 10

# Graph extraction max nodes
MAX_GRAPH_NODES = 30

# Embedding dimensions (all-MiniLM-L6-v2)
EMBEDDING_DIMENSIONS = 384
