"""
Tests for api/v1/events.py — SSE endpoint.

Covers acceptance criteria for TASK-092:
  ✓ GET /events/{resource_id} streams events
  ✓ Response has correct SSE content type and headers
  ✓ Events are forwarded from the notification service
  ✓ Endpoint requires authentication
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.events import router
from app.models.user import User
from app.services.notification import ProgressEvent

# ─── Test app setup ───────────────────────────────────────────────

def _create_test_app(mock_user=None):
    """Create a minimal FastAPI app with the events router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    if mock_user:
        # Override the auth dependency to return our mock user
        from app.core.dependencies import get_current_user
        app.dependency_overrides[get_current_user] = lambda: mock_user

    return app


def _make_mock_user():
    """Create a mock User object."""
    user = MagicMock(spec=User)
    user.id = "user-123"
    user.email = "test@example.com"
    user.username = "testuser"
    user.is_active = True
    return user


# ─── Endpoint Tests ──────────────────────────────────────────────


class TestStreamEvents:
    def test_sse_streams_events(self):
        """GET /events/{resource_id} returns SSE stream with events."""
        mock_user = _make_mock_user()
        app = _create_test_app(mock_user)

        # Mock the subscribe generator to yield two events then stop
        events = [
            ProgressEvent(
                resource_id="src-1",
                status="processing",
                step="parsing",
                pct=50,
            ),
            ProgressEvent(
                resource_id="src-1",
                status="ready",
                step="done",
                pct=100,
            ),
        ]

        async def mock_subscribe(resource_id, **kwargs):
            for event in events:
                yield f"{event.to_sse()}\n\n"

        with patch("app.api.v1.events.subscribe", mock_subscribe):
            client = TestClient(app)
            response = client.get("/api/v1/events/src-1")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["x-accel-buffering"] == "no"

        # Parse the SSE lines from the response body
        body = response.text
        data_lines = [
            line for line in body.strip().split("\n")
            if line.startswith("data: ")
        ]
        assert len(data_lines) == 2

        first = json.loads(data_lines[0].removeprefix("data: "))
        assert first["status"] == "processing"
        assert first["step"] == "parsing"
        assert first["pct"] == 50

        second = json.loads(data_lines[1].removeprefix("data: "))
        assert second["status"] == "ready"

    def test_sse_response_headers(self):
        """Response should have proper SSE headers to prevent buffering."""
        mock_user = _make_mock_user()
        app = _create_test_app(mock_user)

        async def mock_subscribe(resource_id, **kwargs):
            yield "data: {}\n\n"

        with patch("app.api.v1.events.subscribe", mock_subscribe):
            client = TestClient(app)
            response = client.get("/api/v1/events/any-resource")

        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["connection"] == "keep-alive"
        assert response.headers["x-accel-buffering"] == "no"

    def test_sse_requires_auth(self):
        """Without auth override, the endpoint should require authentication."""
        app = FastAPI()
        app.include_router(router, prefix="/api/v1")
        # No dependency override — real auth kicks in

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/api/v1/events/src-1")

        # Should fail with 401 since no Authorization header
        assert response.status_code == 401

    def test_sse_heartbeat_forwarded(self):
        """Heartbeat comments from subscribe() should be forwarded."""
        mock_user = _make_mock_user()
        app = _create_test_app(mock_user)

        async def mock_subscribe(resource_id, **kwargs):
            yield ": heartbeat\n\n"
            yield f"data: {ProgressEvent(resource_id='r1', status='ready').to_sse().removeprefix('data: ')}\n\n"

        # The heartbeat yield has a quirk — let's produce it properly
        async def mock_subscribe_fixed(resource_id, **kwargs):
            yield ": heartbeat\n\n"
            event = ProgressEvent(resource_id="r1", status="ready")
            yield f"{event.to_sse()}\n\n"

        with patch("app.api.v1.events.subscribe", mock_subscribe_fixed):
            client = TestClient(app)
            response = client.get("/api/v1/events/r1")

        body = response.text
        assert ": heartbeat" in body
        assert "data: " in body
