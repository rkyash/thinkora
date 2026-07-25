"""
Tests for services/notification.py — SSE via Redis pub/sub.

Covers all acceptance criteria for TASK-091:
  ✓ Publish event → subscriber receives via SSE
  ✓ Heartbeat sent when no events
  ✓ Stream terminates on "ready" or "error" status
  ✓ Malformed events are handled gracefully
  ✓ ProgressEvent serialization roundtrip
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.notification import (
    CHANNEL_PREFIX,
    ProgressEvent,
    _channel_name,
    publish_event,
    subscribe,
)

# ─── ProgressEvent dataclass ──────────────────────────────────────


class TestProgressEvent:
    def test_defaults(self):
        event = ProgressEvent(resource_id="abc-123", status="processing")
        assert event.resource_id == "abc-123"
        assert event.status == "processing"
        assert event.step == ""
        assert event.pct == -1
        assert event.detail == {}
        assert event.timestamp  # Should have a default timestamp

    def test_to_json_roundtrip(self):
        event = ProgressEvent(
            resource_id="r1",
            status="processing",
            step="chunking",
            pct=40,
            detail={"chunks": 12},
        )
        json_str = event.to_json()
        parsed = json.loads(json_str)
        assert parsed["resource_id"] == "r1"
        assert parsed["status"] == "processing"
        assert parsed["step"] == "chunking"
        assert parsed["pct"] == 40
        assert parsed["detail"] == {"chunks": 12}

    def test_from_json(self):
        raw = json.dumps({
            "resource_id": "x",
            "status": "ready",
            "step": "done",
            "pct": 100,
            "detail": {},
            "timestamp": "2026-01-01T00:00:00",
        })
        event = ProgressEvent.from_json(raw)
        assert event.resource_id == "x"
        assert event.status == "ready"
        assert event.pct == 100

    def test_to_sse(self):
        event = ProgressEvent(resource_id="r1", status="processing", step="parsing")
        sse_line = event.to_sse()
        assert sse_line.startswith("data: ")
        payload = json.loads(sse_line[len("data: "):])
        assert payload["status"] == "processing"

    def test_frozen(self):
        event = ProgressEvent(resource_id="r1", status="processing")
        with pytest.raises(AttributeError):
            event.status = "ready"  # type: ignore[misc]


# ─── Channel naming ──────────────────────────────────────────────


class TestChannelName:
    def test_channel_name(self):
        assert _channel_name("abc-123") == f"{CHANNEL_PREFIX}:abc-123"

    def test_channel_name_uuid(self):
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert _channel_name(uuid) == f"{CHANNEL_PREFIX}:{uuid}"


# ─── publish_event ────────────────────────────────────────────────


class TestPublishEvent:
    @pytest.mark.asyncio
    async def test_publish_sends_to_channel(self):
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=1)

        result = await publish_event(
            "source-1",
            {"status": "processing", "step": "parsing", "pct": 10},
            redis_client=mock_redis,
        )

        assert result == 1
        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        channel = call_args[0][0]
        assert channel == f"{CHANNEL_PREFIX}:source-1"

        # Verify the published data is valid JSON with correct fields
        raw_data = call_args[0][1]
        parsed = json.loads(raw_data)
        assert parsed["resource_id"] == "source-1"
        assert parsed["status"] == "processing"
        assert parsed["step"] == "parsing"
        assert parsed["pct"] == 10

    @pytest.mark.asyncio
    async def test_publish_defaults(self):
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=0)

        await publish_event("res-1", {}, redis_client=mock_redis)

        raw_data = mock_redis.publish.call_args[0][1]
        parsed = json.loads(raw_data)
        assert parsed["status"] == "processing"
        assert parsed["step"] == ""
        assert parsed["pct"] == -1

    @pytest.mark.asyncio
    async def test_publish_creates_redis_if_not_provided(self):
        with patch("app.services.notification.aioredis") as mock_aioredis:
            mock_client = AsyncMock()
            mock_client.publish = AsyncMock(return_value=0)
            mock_aioredis.from_url.return_value = mock_client

            await publish_event("res-1", {"status": "ready"})

            mock_aioredis.from_url.assert_called_once()
            mock_client.publish.assert_called_once()


# ─── subscribe ────────────────────────────────────────────────────


class TestSubscribe:
    def _make_mock_pubsub(self, messages: list[dict | None]):
        """Create a mock pubsub that returns messages in sequence."""
        pubsub = AsyncMock()
        pubsub.subscribe = AsyncMock()
        pubsub.unsubscribe = AsyncMock()
        pubsub.aclose = AsyncMock()

        message_iter = iter(messages)

        async def get_message_side_effect(**kwargs):
            try:
                return next(message_iter)
            except StopIteration:
                # Signal end by raising CancelledError
                raise asyncio.CancelledError

        pubsub.get_message = AsyncMock(side_effect=get_message_side_effect)
        return pubsub

    def _make_mock_redis(self, pubsub):
        """Create a mock Redis client where .pubsub() is synchronous."""
        mock_redis = MagicMock()
        mock_redis.pubsub.return_value = pubsub
        return mock_redis

    @pytest.mark.asyncio
    async def test_subscribe_yields_events(self):
        event_data = ProgressEvent(
            resource_id="src-1",
            status="ready",
            step="done",
            pct=100,
        ).to_json()

        pubsub = self._make_mock_pubsub([
            {"type": "message", "data": event_data},
        ])
        mock_redis = self._make_mock_redis(pubsub)

        events = []
        async for sse_line in subscribe("src-1", redis_client=mock_redis):
            events.append(sse_line)

        # Should get exactly one event (terminal "ready" closes stream)
        assert len(events) == 1
        assert events[0].startswith("data: ")
        assert events[0].endswith("\n\n")
        parsed = json.loads(events[0].strip().removeprefix("data: "))
        assert parsed["status"] == "ready"

    @pytest.mark.asyncio
    async def test_subscribe_heartbeat_on_timeout(self):
        """When no messages arrive, heartbeat comments should be yielded."""
        pubsub = AsyncMock()
        pubsub.subscribe = AsyncMock()
        pubsub.unsubscribe = AsyncMock()
        pubsub.aclose = AsyncMock()

        call_count = 0

        async def get_message_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None  # No message → heartbeat
            if call_count == 2:
                # Return a terminal event to stop the stream
                return {
                    "type": "message",
                    "data": ProgressEvent(
                        resource_id="src-1", status="ready"
                    ).to_json(),
                }
            raise asyncio.CancelledError

        pubsub.get_message = AsyncMock(side_effect=get_message_side_effect)
        mock_redis = self._make_mock_redis(pubsub)

        events = []
        async for sse_line in subscribe(
            "src-1", heartbeat_seconds=1, redis_client=mock_redis
        ):
            events.append(sse_line)

        assert events[0] == ": heartbeat\n\n"
        assert len(events) == 2  # heartbeat + terminal event

    @pytest.mark.asyncio
    async def test_subscribe_terminates_on_error_status(self):
        event_data = ProgressEvent(
            resource_id="src-1",
            status="error",
            detail={"message": "parse failed"},
        ).to_json()

        pubsub = self._make_mock_pubsub([
            {"type": "message", "data": event_data},
        ])
        mock_redis = self._make_mock_redis(pubsub)

        events = []
        async for sse_line in subscribe("src-1", redis_client=mock_redis):
            events.append(sse_line)

        assert len(events) == 1
        parsed = json.loads(events[0].strip().removeprefix("data: "))
        assert parsed["status"] == "error"

    @pytest.mark.asyncio
    async def test_subscribe_continues_on_non_terminal(self):
        """Non-terminal events should keep the stream open."""
        events_data = [
            ProgressEvent(
                resource_id="s1", status="processing", step="parsing", pct=25
            ).to_json(),
            ProgressEvent(
                resource_id="s1", status="processing", step="chunking", pct=50
            ).to_json(),
            ProgressEvent(
                resource_id="s1", status="ready", step="done", pct=100
            ).to_json(),
        ]

        pubsub = self._make_mock_pubsub([
            {"type": "message", "data": events_data[0]},
            {"type": "message", "data": events_data[1]},
            {"type": "message", "data": events_data[2]},
        ])
        mock_redis = self._make_mock_redis(pubsub)

        events = []
        async for sse_line in subscribe("s1", redis_client=mock_redis):
            events.append(sse_line)

        assert len(events) == 3
        # Verify progress order
        statuses = []
        for e in events:
            parsed = json.loads(e.strip().removeprefix("data: "))
            statuses.append(parsed["step"])
        assert statuses == ["parsing", "chunking", "done"]

    @pytest.mark.asyncio
    async def test_subscribe_skips_subscribe_messages(self):
        """Subscribe confirmation messages from Redis should be ignored."""
        event_data = ProgressEvent(
            resource_id="s1", status="ready"
        ).to_json()

        pubsub = self._make_mock_pubsub([
            {"type": "subscribe", "data": 1},  # Redis subscribe confirmation
            {"type": "message", "data": event_data},
        ])
        mock_redis = self._make_mock_redis(pubsub)

        events = []
        async for sse_line in subscribe("s1", redis_client=mock_redis):
            events.append(sse_line)

        # Only the actual message should be yielded, not the subscribe confirmation
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_subscribe_handles_malformed_json(self):
        """Malformed JSON should still be forwarded as raw data."""
        pubsub = self._make_mock_pubsub([
            {"type": "message", "data": "not-valid-json{{{"},
        ])
        mock_redis = self._make_mock_redis(pubsub)

        events = []
        # Stream won't auto-terminate since the malformed event
        # can't be checked for terminal status. It'll raise CancelledError
        # on the next get_message call.
        async for sse_line in subscribe("s1", redis_client=mock_redis):
            events.append(sse_line)

        assert len(events) == 1
        assert "not-valid-json{{{" in events[0]

    @pytest.mark.asyncio
    async def test_subscribe_cleans_up_on_cancel(self):
        """Pubsub should be unsubscribed and closed on client disconnect."""
        pubsub = AsyncMock()
        pubsub.subscribe = AsyncMock()
        pubsub.unsubscribe = AsyncMock()
        pubsub.aclose = AsyncMock()
        pubsub.get_message = AsyncMock(side_effect=asyncio.CancelledError)

        mock_redis = self._make_mock_redis(pubsub)

        events = []
        async for sse_line in subscribe("s1", redis_client=mock_redis):
            events.append(sse_line)

        pubsub.unsubscribe.assert_called_once()
        pubsub.aclose.assert_called_once()
