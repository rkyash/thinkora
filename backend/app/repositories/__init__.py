"""
Repository package — domain-specific data access layer.
"""

from app.repositories.chat_session import ChatSessionRepo
from app.repositories.chunk import ChunkRepo
from app.repositories.flashcard import FlashcardRepo
from app.repositories.generation import GenerationRepo
from app.repositories.message import MessageRepo
from app.repositories.note import NoteRepo
from app.repositories.notebook import NotebookRepo
from app.repositories.quiz import QuizRepo
from app.repositories.source import SourceRepo
from app.repositories.user import UserRepo
from app.repositories.workspace import WorkspaceRepo

# Singleton repo instances — import these in services
user_repo = UserRepo()
workspace_repo = WorkspaceRepo()
notebook_repo = NotebookRepo()
source_repo = SourceRepo()
chunk_repo = ChunkRepo()
chat_session_repo = ChatSessionRepo()
message_repo = MessageRepo()
note_repo = NoteRepo()
flashcard_repo = FlashcardRepo()
quiz_repo = QuizRepo()
generation_repo = GenerationRepo()

__all__ = [
    "user_repo",
    "workspace_repo",
    "notebook_repo",
    "source_repo",
    "chunk_repo",
    "chat_session_repo",
    "message_repo",
    "note_repo",
    "flashcard_repo",
    "quiz_repo",
    "generation_repo",
]
