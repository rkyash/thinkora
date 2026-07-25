"""
Tests for api/v1/sources.py — Sources API.

Covers acceptance criteria for TASK-110:
  ✓ POST /upload creates file source and triggers ingestion
  ✓ POST /url creates URL source and triggers ingestion
  ✓ POST /youtube creates YouTube source and triggers ingestion
  ✓ POST /text creates text source and triggers ingestion
  ✓ GET / lists sources
  ✓ GET /{id} retrieves source
  ✓ DELETE /{id} deletes source and associated data
"""

from __future__ import annotations

import uuid
from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.sources import router
from app.core.dependencies import get_current_user, get_db
from app.models.user import User


def _create_test_app(mock_user=None):
    """Create a minimal FastAPI app with the sources router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    if mock_user is None:
        mock_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="fake",
            is_active=True,
        )

    async def override_get_user():
        return mock_user

    async def override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_current_user] = override_get_user
    app.dependency_overrides[get_db] = override_get_db

    return app, mock_user


@pytest.fixture
def client_and_user():
    app, user = _create_test_app()
    client = TestClient(app)
    return client, user


@pytest.fixture
def mock_deps():
    with (
        patch("app.api.v1.sources.workspace_repo.get_or_404") as mock_workspace_get,
        patch("app.api.v1.sources.notebook_repo.get_or_404") as mock_notebook_get,
        patch("app.api.v1.sources.source_repo.create") as mock_source_create,
        patch("app.api.v1.sources.source_repo.list_by_notebook") as mock_source_list,
        patch("app.api.v1.sources.source_repo.count", new_callable=AsyncMock) as mock_source_count,
        patch("app.api.v1.sources.source_repo.get_or_404") as mock_source_get,
        patch("app.api.v1.sources.source_repo.delete") as mock_source_delete,
        patch("app.api.v1.sources.get_storage") as mock_get_storage,
        patch("app.api.v1.sources.ingest_source_task") as mock_ingest_task,
        patch("app.api.v1.sources.chunk_repo.delete_by_source") as mock_chunk_delete,
        patch("app.api.v1.sources.get_vector_store") as mock_get_vector_store,
    ):
        mock_workspace_get.return_value = MagicMock(owner_id=None)  # We'll set this in the test
        mock_notebook_get.return_value = MagicMock(workspace_id="ws_id", id="nb_id")
        mock_source_count.return_value = 1  # Return an int so has_next comparison works

        mock_storage = AsyncMock()
        mock_storage.save.return_value = "path/to/file"
        mock_get_storage.return_value = mock_storage

        mock_vector_store = AsyncMock()
        mock_get_vector_store.return_value = mock_vector_store

        yield {
            "workspace_get": mock_workspace_get,
            "notebook_get": mock_notebook_get,
            "source_create": mock_source_create,
            "source_list": mock_source_list,
            "source_count": mock_source_count,
            "source_get": mock_source_get,
            "source_delete": mock_source_delete,
            "storage": mock_storage,
            "ingest_task": mock_ingest_task,
            "chunk_delete": mock_chunk_delete,
            "vector_store": mock_vector_store,
        }


def get_mock_source():
    import uuid
    from datetime import datetime, timezone

    from app.core.constants import SourceStatus, SourceType
    from app.models.source import Source

    return Source(
        id=uuid.uuid4(),
        notebook_id=uuid.uuid4(),
        name="test_source",
        type=SourceType.TXT,
        status=SourceStatus.PENDING,
        created_at=datetime.now(UTC),
    )


class TestSourcesAPI:
    def test_upload_source(self, client_and_user, mock_deps):
        client, user = client_and_user
        mock_deps["workspace_get"].return_value.owner_id = user.id

        mock_source = get_mock_source()
        mock_deps["source_create"].return_value = mock_source

        response = client.post(
            "/api/v1/notebooks/nb_id/sources/upload?workspace_id=ws_id",
            files={"file": ("test.pdf", b"pdf content", "application/pdf")},
        )

        assert response.status_code == 201
        assert response.json()["success"] is True
        mock_deps["storage"].save.assert_called_once()
        mock_deps["source_create"].assert_called_once()
        mock_deps["ingest_task"].delay.assert_called_once_with(str(mock_source.id))

    def test_create_url_source(self, client_and_user, mock_deps):
        client, user = client_and_user
        mock_deps["workspace_get"].return_value.owner_id = user.id

        mock_source = get_mock_source()
        mock_deps["source_create"].return_value = mock_source

        response = client.post(
            "/api/v1/notebooks/nb_id/sources/url?workspace_id=ws_id",
            json={"name": "My URL", "url": "https://example.com"},
        )

        assert response.status_code == 201
        assert response.json()["success"] is True
        mock_deps["source_create"].assert_called_once()
        mock_deps["ingest_task"].delay.assert_called_once_with(str(mock_source.id))

    def test_create_youtube_source(self, client_and_user, mock_deps):
        client, user = client_and_user
        mock_deps["workspace_get"].return_value.owner_id = user.id

        mock_source = get_mock_source()
        mock_deps["source_create"].return_value = mock_source

        response = client.post(
            "/api/v1/notebooks/nb_id/sources/youtube?workspace_id=ws_id",
            json={"name": "My YT Video", "url": "https://youtube.com/watch?v=123"},
        )

        assert response.status_code == 201
        assert response.json()["success"] is True
        mock_deps["source_create"].assert_called_once()
        mock_deps["ingest_task"].delay.assert_called_once_with(str(mock_source.id))

    def test_create_text_source(self, client_and_user, mock_deps):
        client, user = client_and_user
        mock_deps["workspace_get"].return_value.owner_id = user.id

        mock_source = get_mock_source()
        mock_deps["source_create"].return_value = mock_source

        response = client.post(
            "/api/v1/notebooks/nb_id/sources/text?workspace_id=ws_id",
            json={"name": "My Note", "content": "Hello World"},
        )

        assert response.status_code == 201
        assert response.json()["success"] is True
        mock_deps["storage"].save.assert_called_once()
        mock_deps["source_create"].assert_called_once()
        mock_deps["ingest_task"].delay.assert_called_once_with(str(mock_source.id))

    def test_list_sources(self, client_and_user, mock_deps):
        client, user = client_and_user
        mock_deps["workspace_get"].return_value.owner_id = user.id

        mock_source = get_mock_source()
        mock_deps["source_list"].return_value = [mock_source]

        response = client.get(
            "/api/v1/notebooks/nb_id/sources/?workspace_id=ws_id",
        )

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert len(response.json()["data"]) == 1

    def test_get_source(self, client_and_user, mock_deps):
        client, user = client_and_user
        mock_deps["workspace_get"].return_value.owner_id = user.id

        mock_source = get_mock_source()
        mock_deps["notebook_get"].return_value = MagicMock(
            workspace_id="ws_id", id=mock_source.notebook_id
        )
        mock_deps["source_get"].return_value = mock_source

        response = client.get(
            f"/api/v1/notebooks/{mock_source.notebook_id}/sources/{mock_source.id}?workspace_id=ws_id",
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_delete_source(self, client_and_user, mock_deps):
        client, user = client_and_user
        mock_deps["workspace_get"].return_value.owner_id = user.id

        mock_source = get_mock_source()
        mock_deps["notebook_get"].return_value = MagicMock(
            workspace_id="ws_id", id=mock_source.notebook_id
        )
        mock_source.file_path = "path"
        mock_deps["source_get"].return_value = mock_source

        response = client.delete(
            f"/api/v1/notebooks/{mock_source.notebook_id}/sources/{mock_source.id}?workspace_id=ws_id",
        )

        # 204 No Content — response body must be empty
        assert response.status_code == 204
        assert response.content == b""
        mock_deps["storage"].delete.assert_called_once_with("path")
        mock_deps["chunk_delete"].assert_called_once()
        mock_deps["vector_store"].delete_by_source.assert_called_once()
        mock_deps["source_delete"].assert_called_once()
