"""
Notification service — Server-Sent Events (SSE) via Redis pub/sub.

Workers publish progress events to Redis channels, and the SSE endpoint
subscribes on behalf of the frontend client.

Usage (publisher side — in Celery tasks):
    from app.services.notification import publish_event

    await publish_event(resource_id, {
        "status": "processing",
        "step": "chunking",
        "pct": 40,
    })

Usage (subscriber side — in SSE endpoint):
    from app.services.notification import subscribe

    async for event in subscribe(resource_id):
        yield event  # SSE data line
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any

import redis.asyncio as aioredis

from app.config import settings
from app.core.logging import logger

# ─── Constants ────────────────────────────────────────────────────

CHANNEL_PREFIX = "events"
HEARTBEAT_INTERVAL_SECONDS = 15


# ─── Event Data Model ────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """Structured progress event pushed through the SSE channel.

    Attributes:
        resource_id: The UUID of the resource this event relates to.
        status: Current lifecycle status (e.g. "processing", "ready", "error").
        step: Human-readable label for the current pipeline step.
        pct: Progress percentage (0–100). ``-1`` means indeterminate.
        detail: Optional extra information (error messages, metadata).
        timestamp: ISO-8601 timestamp when the event was created.
    """

    resource_id: str
    status: str
    step: str = ""
    pct: int = -1
    detail: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )

    def to_json(self) -> str:
        """Serialize to a JSON string for Redis transport."""
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str) -> ProgressEvent:
        """Deserialize from a JSON string."""
        data = json.loads(raw)
        return cls(**data)

    def to_sse(self) -> str:
        """Format as an SSE ``data:`` line (without the trailing newlines)."""
        return f"data: {self.to_json()}"


# ─── Channel Helpers ──────────────────────────────────────────────


def _channel_name(resource_id: str) -> str:
    """Build the Redis pub/sub channel name for a given resource."""
    return f"{CHANNEL_PREFIX}:{resource_id}"


# ─── Publish (worker / service side) ─────────────────────────────


async def publish_event(
    resource_id: str,
    data: dict[str, Any],
    *,
    redis_client: aioredis.Redis | None = None,
) -> int:
    """
    Publish a progress event to the Redis channel for *resource_id*.

    Args:
        resource_id: UUID string identifying the resource (source, generation, etc.).
        data: Event payload — should include at minimum ``status`` and optionally
              ``step``, ``pct``, ``detail``.
        redis_client: Optional pre-existing Redis client (useful in workers that
                      maintain their own connection).

    Returns:
        Number of subscribers who received the message.
    """
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )

    event = ProgressEvent(
        resource_id=resource_id,
        status=data.get("status", "processing"),
        step=data.get("step", ""),
        pct=data.get("pct", -1),
        detail=data.get("detail", {}),
    )

    channel = _channel_name(resource_id)
    num_receivers = await redis_client.publish(channel, event.to_json())

    logger.debug(
        "event_published",
        channel=channel,
        status=event.status,
        step=event.step,
        pct=event.pct,
        receivers=num_receivers,
    )
    return num_receivers


async def publish_event_sync(
    resource_id: str,
    data: dict[str, Any],
) -> int:
    """
    Synchronous-friendly wrapper for publishing events from Celery workers.

    Creates a temporary Redis connection, publishes, and disconnects.
    Intended to be called via ``asyncio.run()`` from synchronous task code.
    """
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        return await publish_event(resource_id, data, redis_client=client)
    finally:
        await client.aclose()


# ─── Subscribe (SSE endpoint side) ───────────────────────────────


async def subscribe(
    resource_id: str,
    *,
    heartbeat_seconds: int = HEARTBEAT_INTERVAL_SECONDS,
    redis_client: aioredis.Redis | None = None,
) -> AsyncIterator[str]:
    """
    Subscribe to progress events for *resource_id* and yield SSE-formatted lines.

    This is an async generator designed to be consumed directly by a
    ``StreamingResponse`` in the SSE endpoint.

    The generator:
      - Yields ``data: {...}\\n\\n`` lines for each event.
      - Sends a heartbeat comment (``:``) every *heartbeat_seconds* to keep
        the connection alive and detect stale clients.
      - Terminates when a ``"ready"`` or ``"error"`` status is received.

    Args:
        resource_id: UUID of the resource to subscribe to.
        heartbeat_seconds: Interval between keep-alive heartbeat comments.
        redis_client: Optional pre-existing Redis client.

    Yields:
        SSE-formatted strings (each ending with ``\\n\\n``).
    """
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )

    channel = _channel_name(resource_id)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    logger.info("sse_subscribe", channel=channel, resource_id=resource_id)

    try:
        while True:
            try:
                message = await asyncio.wait_for(
                    pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=heartbeat_seconds,
                    ),
                    timeout=heartbeat_seconds + 1,
                )
            except TimeoutError:
                message = None

            if message is None:
                # No message within the heartbeat window — send keep-alive
                yield ": heartbeat\n\n"
                continue

            if message["type"] != "message":
                continue

            raw_data = message["data"]

            try:
                event = ProgressEvent.from_json(raw_data)
                yield f"{event.to_sse()}\n\n"

                # Terminal states — close the stream
                if event.status in ("ready", "error"):
                    logger.info(
                        "sse_stream_complete",
                        channel=channel,
                        terminal_status=event.status,
                    )
                    return

            except (json.JSONDecodeError, TypeError) as exc:
                logger.warning(
                    "sse_malformed_event",
                    channel=channel,
                    raw=raw_data,
                    error=str(exc),
                )
                # Forward raw data as-is so the client still gets something
                yield f"data: {raw_data}\n\n"

    except asyncio.CancelledError:
        logger.info("sse_client_disconnected", channel=channel)
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        logger.debug("sse_unsubscribed", channel=channel)
