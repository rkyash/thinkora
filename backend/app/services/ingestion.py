"""
Ingestion service — pipeline orchestrator for source document processing.

Coordinates the full lifecycle of a source: fetch → parse → chunk → embed →
store vectors → persist DB records → publish progress events.

Usage (from a Celery worker or API handler):
    async with async_session() as db:
        svc = IngestionService(db)
        await svc.ingest_source(source_id)
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    SourceStatus,
    SourceType,
)
from app.core.logging import logger
from app.repositories.chunk import ChunkRepo
from app.repositories.source import SourceRepo
from app.services.embedding import get_embedding_service
from app.services.notification import publish_event
from app.services.parsers import dispatch_parser
from app.services.storage import get_storage
from app.services.vector_store import get_vector_store

# ─── Text Chunking ───────────────────────────────────────────────────


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split *text* into overlapping chunks by sentences.

    The function splits on sentence boundaries (period / question mark /
    exclamation mark followed by whitespace) and then accumulates sentences
    into chunks that stay within *chunk_size* characters.  Each successive
    chunk begins *overlap* characters before the previous chunk ended to
    maintain context continuity.

    Args:
        text: The full document text to chunk.
        chunk_size: Target maximum character length per chunk.
        overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        A list of text chunks.  Empty list if *text* is empty.
    """
    if not text or not text.strip():
        return []

    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        # If adding this sentence would exceed the chunk size,
        # flush the current chunk first
        if current_length + sentence_len > chunk_size and current_chunk:
            chunk_text_str = " ".join(current_chunk)
            chunks.append(chunk_text_str)

            # Build the overlap window: keep trailing sentences that fit
            # within the overlap budget
            overlap_sentences: list[str] = []
            overlap_length = 0
            for s in reversed(current_chunk):
                if overlap_length + len(s) > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_length += len(s) + 1  # +1 for space

            current_chunk = overlap_sentences
            current_length = sum(len(s) for s in current_chunk) + max(
                0, len(current_chunk) - 1
            )

        current_chunk.append(sentence)
        current_length += sentence_len + (1 if len(current_chunk) > 1 else 0)

    # Flush remaining sentences
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# ─── Source types that use URL content directly ─────────────────────

_URL_SOURCE_TYPES = {SourceType.URL, SourceType.YOUTUBE}


# ─── Ingestion Service ───────────────────────────────────────────────


class IngestionService:
    """Orchestrates the full document ingestion pipeline.

    Lifecycle::

        pending → processing → (parse → chunk → embed → store) → ready
                                                                  ↘ error
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._source_repo = SourceRepo()
        self._chunk_repo = ChunkRepo()

    # ── main entry point ──────────────────────────────────────

    async def ingest_source(self, source_id: str) -> None:
        """Run the full ingestion pipeline for a single source.

        Steps:
          1. Mark source as PROCESSING
          2. Parse raw content
          3. Chunk the extracted text
          4. Generate embeddings
          5. Upsert vectors to Qdrant
          6. Persist DocumentChunk rows
          7. Mark source as READY

        On failure the source is marked ERROR with the exception message.
        """
        source = None
        try:
            # ── 1. Fetch & mark PROCESSING ────────────────────
            source = await self._source_repo.get_or_404(self._db, source_id)

            await self._source_repo.update_status(
                self._db, source_id, SourceStatus.PROCESSING
            )
            await self._db.commit()

            await publish_event(
                source_id,
                {"status": "processing", "step": "parsing", "pct": 10},
            )

            logger.info(
                "ingestion_started",
                source_id=source_id,
                source_type=source.type.value,
            )

            # ── 2. Load raw data ──────────────────────────────
            if source.type in _URL_SOURCE_TYPES:
                # For URL / YouTube sources the "data" is the URL itself
                raw_data = (source.url or "").encode("utf-8")
            else:
                storage = get_storage()
                raw_data = await storage.load(source.file_path)  # type: ignore[arg-type]

            # ── 3. Parse ──────────────────────────────────────
            parser = dispatch_parser(source.type)
            text = await parser.parse(raw_data, filename=source.name or "")

            await publish_event(
                source_id,
                {"status": "processing", "step": "chunking", "pct": 30},
            )

            # ── 4. Chunk ──────────────────────────────────────
            chunks = chunk_text(text, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP)

            if not chunks:
                logger.warning(
                    "ingestion_no_chunks",
                    source_id=source_id,
                )
                chunks = [text] if text.strip() else []

            await publish_event(
                source_id,
                {"status": "processing", "step": "embedding", "pct": 50},
            )

            # ── 5. Embed ──────────────────────────────────────
            embedding_svc = get_embedding_service()
            vectors = embedding_svc.embed_texts(chunks)

            await publish_event(
                source_id,
                {"status": "processing", "step": "storing", "pct": 70},
            )

            # ── 6. Upsert to Qdrant ──────────────────────────
            vector_store = get_vector_store()
            await vector_store.ensure_collection(source.notebook_id)

            points: list[dict[str, Any]] = []
            point_ids: list[str] = []
            for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                point_id = str(uuid.uuid4())
                point_ids.append(point_id)
                points.append(
                    {
                        "id": point_id,
                        "vector": vector,
                        "payload": {
                            "source_id": source_id,
                            "chunk_index": idx,
                            "text_preview": chunk[:200],
                        },
                    }
                )

            await vector_store.upsert(source.notebook_id, points)

            # ── 7. Persist DocumentChunk rows ─────────────────
            chunk_rows: list[dict[str, Any]] = [
                {
                    "source_id": source_id,
                    "notebook_id": source.notebook_id,
                    "content": chunk,
                    "chunk_index": idx,
                    "token_count": len(chunk.split()),
                    "qdrant_point_id": point_ids[idx],
                }
                for idx, chunk in enumerate(chunks)
            ]

            await self._chunk_repo.bulk_create(self._db, chunk_rows)

            # ── 8. Finalise source ────────────────────────────
            await self._source_repo.update_status(
                self._db,
                source_id,
                SourceStatus.READY,
                char_count=len(text),
                chunk_count=len(chunks),
            )
            await self._db.commit()

            await publish_event(
                source_id,
                {"status": "ready", "pct": 100},
            )

            logger.info(
                "ingestion_complete",
                source_id=source_id,
                char_count=len(text),
                chunk_count=len(chunks),
            )

        except Exception as exc:
            logger.error(
                "ingestion_failed",
                source_id=source_id,
                error=str(exc),
                exc_info=True,
            )

            # Roll back any partial writes in this session
            await self._db.rollback()

            # Mark the source as ERROR (if we managed to fetch it)
            if source is not None:
                try:
                    await self._source_repo.update_status(
                        self._db,
                        source_id,
                        SourceStatus.ERROR,
                        error_message=str(exc)[:500],
                    )
                    await self._db.commit()
                except Exception as status_exc:
                    logger.error(
                        "ingestion_status_update_failed",
                        source_id=source_id,
                        error=str(status_exc),
                    )

            await publish_event(
                source_id,
                {
                    "status": "error",
                    "step": "failed",
                    "pct": -1,
                    "detail": {"error": str(exc)[:500]},
                },
            )

            raise
