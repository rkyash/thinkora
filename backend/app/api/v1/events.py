"""
SSE events endpoint — streams real-time progress for long-running tasks.

Clients subscribe via:
    GET /api/v1/events/{resource_id}

The endpoint opens a Server-Sent Events stream backed by Redis pub/sub.
Workers publish progress events to the channel, and this endpoint relays
them to the connected client.

Event format:
    data: {"resource_id": "...", "status": "processing", "step": "chunking", "pct": 40, ...}
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_current_user_for_sse
from app.core.logging import logger
from app.models.user import User
from app.services.notification import subscribe

router = APIRouter(prefix="/events", tags=["Events"])


@router.get(
    "/{resource_id}",
    summary="Subscribe to real-time progress events",
    description=(
        "Opens a Server-Sent Events (SSE) stream for the given resource. "
        "The stream emits progress events as JSON payloads and automatically "
        "closes when the resource reaches a terminal state (`ready` or `error`). "
        "A heartbeat comment is sent every ~15 seconds to keep the connection alive."
    ),
    responses={
        200: {
            "description": "SSE event stream",
            "content": {"text/event-stream": {}},
        },
    },
)
async def stream_events(
    resource_id: str,
    request: Request,
    offset: int = Query(0, ge=0, description="Ignored for SSE streams"),
    limit: int = Query(100, ge=1, le=1000, description="Ignored for SSE streams"),
    current_user: User = Depends(get_current_user_for_sse),
) -> StreamingResponse:
    """Stream SSE progress events for a long-running task.

    Used by the frontend to show real-time progress for:
    - Source ingestion (parsing → chunking → embedding → ready)
    - Content generation (summary, quiz, flashcards, study guide)
    - Podcast generation (script → TTS → stitch → ready)
    """
    logger.info(
        "sse_stream_requested",
        resource_id=resource_id,
        user_id=current_user.id,
        offset=offset,
        limit=limit,
    )

    async def event_generator():
        """Wrap subscribe() with client disconnect detection."""
        async for sse_line in subscribe(resource_id):
            # Check if client has disconnected
            if await request.is_disconnected():
                logger.info(
                    "sse_client_disconnected",
                    resource_id=resource_id,
                    user_id=current_user.id,
                )
                break
            yield sse_line

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )