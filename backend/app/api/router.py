"""
API v1 router — mounts all v1 route modules under /api/v1.
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.events import router as events_router
from app.api.v1.notebooks import router as notebooks_router, router_direct as notebooks_router_direct
from app.api.v1.sources import router as sources_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.chat import router as chat_router

# Phase 3 — Study Tools, Graph, Search, Generation
from app.api.v1.notes import router as notes_router
from app.api.v1.flashcards import router as flashcards_router
from app.api.v1.quizzes import router as quizzes_router
from app.api.v1.graph import router as graph_router
from app.api.v1.search import router as search_router
from app.api.v1.generate import router as generate_router
from app.api.v1.settings import router as settings_router
from app.api.v1.audio import router as audio_router

api_router = APIRouter()

# Foundation + Ingestion + RAG
api_router.include_router(auth_router)
api_router.include_router(events_router)
api_router.include_router(workspaces_router)
api_router.include_router(notebooks_router)
api_router.include_router(notebooks_router_direct)
api_router.include_router(sources_router)
api_router.include_router(chat_router)

# Study Tools + Graph + Notes + Search
api_router.include_router(notes_router)
api_router.include_router(flashcards_router)
api_router.include_router(quizzes_router)
api_router.include_router(graph_router)
api_router.include_router(search_router)
api_router.include_router(generate_router)

# Settings + Config + Audio
api_router.include_router(settings_router)
api_router.include_router(audio_router)
