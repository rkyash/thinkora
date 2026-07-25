"""
SQLAlchemy ORM model registry.
Import all models here so Alembic can discover them.
"""

from app.models.user import User
from app.models.workspace import Workspace
from app.models.notebook import Notebook
from app.models.source import Source
from app.models.chunk import DocumentChunk
from app.models.chat_session import ChatSession
from app.models.message import ChatMessage
from app.models.note import Note
from app.models.flashcard import Flashcard
from app.models.quiz import Quiz, QuizQuestion
from app.models.graph_node import GraphNode
from app.models.graph_edge import GraphEdge
from app.models.generation import Generation
from app.models.app_settings import AppSetting

__all__ = [
    "User",
    "Workspace",
    "Notebook",
    "Source",
    "DocumentChunk",
    "ChatSession",
    "ChatMessage",
    "Note",
    "Flashcard",
    "Quiz",
    "QuizQuestion",
    "GraphNode",
    "GraphEdge",
    "Generation",
    "AppSetting",
]
