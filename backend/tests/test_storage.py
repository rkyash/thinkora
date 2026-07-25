"""
Tests for services/storage.py — LocalStorage backend.

Covers all acceptance criteria for TASK-090:
  ✓ save, load, delete, exists operations
  ✓ Operations target ~/.thinkora/ (or test tmp dir)
  ✓ Path traversal protection
  ✓ Idempotent deletes
  ✓ Factory function
"""

from __future__ import annotations

import pytest

from app.services.storage import LocalStorage, get_storage, reset_storage


@pytest.fixture()
def storage(tmp_path):
    """Create a LocalStorage rooted in a temporary directory."""
    return LocalStorage(root=tmp_path)


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Ensure the global storage singleton is reset between tests."""
    reset_storage()
    yield
    reset_storage()


# ─── save ──────────────────────────────────────────────────────────


class TestSave:
    @pytest.mark.asyncio
    async def test_save_creates_file(self, storage, tmp_path):
        path = await storage.save("sources/test.txt", b"hello world")
        assert path == "sources/test.txt"
        assert (tmp_path / "sources" / "test.txt").read_bytes() == b"hello world"

    @pytest.mark.asyncio
    async def test_save_creates_nested_dirs(self, storage, tmp_path):
        await storage.save("a/b/c/deep.bin", b"\x00\x01\x02")
        assert (tmp_path / "a" / "b" / "c" / "deep.bin").exists()

    @pytest.mark.asyncio
    async def test_save_overwrites_existing(self, storage, tmp_path):
        await storage.save("file.txt", b"v1")
        await storage.save("file.txt", b"v2")
        assert (tmp_path / "file.txt").read_bytes() == b"v2"

    @pytest.mark.asyncio
    async def test_save_empty_file(self, storage, tmp_path):
        await storage.save("empty.bin", b"")
        assert (tmp_path / "empty.bin").read_bytes() == b""

    @pytest.mark.asyncio
    async def test_save_returns_path(self, storage):
        result = await storage.save("my/file.pdf", b"pdf-bytes")
        assert result == "my/file.pdf"


# ─── load ──────────────────────────────────────────────────────────


class TestLoad:
    @pytest.mark.asyncio
    async def test_load_returns_bytes(self, storage):
        await storage.save("data.bin", b"\xff\xfe")
        data = await storage.load("data.bin")
        assert data == b"\xff\xfe"

    @pytest.mark.asyncio
    async def test_load_nonexistent_raises(self, storage):
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await storage.load("does_not_exist.txt")

    @pytest.mark.asyncio
    async def test_load_large_content(self, storage):
        big = b"x" * (1024 * 1024)  # 1 MB
        await storage.save("big.bin", big)
        loaded = await storage.load("big.bin")
        assert loaded == big


# ─── delete ────────────────────────────────────────────────────────


class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_removes_file(self, storage, tmp_path):
        await storage.save("to_delete.txt", b"gone")
        assert (tmp_path / "to_delete.txt").exists()

        await storage.delete("to_delete.txt")
        assert not (tmp_path / "to_delete.txt").exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_is_noop(self, storage):
        # Should not raise
        await storage.delete("never_existed.txt")

    @pytest.mark.asyncio
    async def test_delete_cleans_empty_parents(self, storage, tmp_path):
        await storage.save("a/b/c/file.txt", b"data")
        await storage.delete("a/b/c/file.txt")
        # Empty parent dirs should be cleaned up
        assert not (tmp_path / "a" / "b" / "c").exists()

    @pytest.mark.asyncio
    async def test_delete_preserves_nonempty_parents(self, storage, tmp_path):
        await storage.save("dir/file1.txt", b"keep")
        await storage.save("dir/file2.txt", b"delete me")
        await storage.delete("dir/file2.txt")
        # dir/ still has file1.txt so it should remain
        assert (tmp_path / "dir").exists()
        assert (tmp_path / "dir" / "file1.txt").exists()


# ─── exists ────────────────────────────────────────────────────────


class TestExists:
    @pytest.mark.asyncio
    async def test_exists_true_when_present(self, storage):
        await storage.save("present.txt", b"here")
        assert await storage.exists("present.txt") is True

    @pytest.mark.asyncio
    async def test_exists_false_when_missing(self, storage):
        assert await storage.exists("missing.txt") is False

    @pytest.mark.asyncio
    async def test_exists_false_after_delete(self, storage):
        await storage.save("temp.txt", b"temp")
        await storage.delete("temp.txt")
        assert await storage.exists("temp.txt") is False

    @pytest.mark.asyncio
    async def test_exists_false_for_directory(self, storage, tmp_path):
        (tmp_path / "some_dir").mkdir()
        # exists() should only report files, not directories
        assert await storage.exists("some_dir") is False


# ─── list_dir ──────────────────────────────────────────────────────


class TestListDir:
    @pytest.mark.asyncio
    async def test_list_dir_empty(self, storage):
        result = await storage.list_dir()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_dir_returns_files(self, storage):
        await storage.save("a.txt", b"a")
        await storage.save("sub/b.txt", b"b")
        result = await storage.list_dir()
        assert "a.txt" in result
        assert "sub/b.txt" in result

    @pytest.mark.asyncio
    async def test_list_dir_with_prefix(self, storage):
        await storage.save("audio/ep1.mp3", b"1")
        await storage.save("audio/ep2.mp3", b"2")
        await storage.save("sources/doc.pdf", b"3")
        result = await storage.list_dir("audio")
        assert len(result) == 2
        assert all("audio" in r for r in result)


# ─── size ──────────────────────────────────────────────────────────


class TestSize:
    @pytest.mark.asyncio
    async def test_size_returns_correct_value(self, storage):
        data = b"twelve bytes"
        await storage.save("sized.txt", data)
        assert await storage.size("sized.txt") == len(data)

    @pytest.mark.asyncio
    async def test_size_nonexistent_raises(self, storage):
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await storage.size("nope.txt")


# ─── path traversal ───────────────────────────────────────────────


class TestSecurity:
    @pytest.mark.asyncio
    async def test_traversal_blocked_on_save(self, storage):
        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await storage.save("../../etc/passwd", b"evil")

    @pytest.mark.asyncio
    async def test_traversal_blocked_on_load(self, storage):
        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await storage.load("../../../etc/shadow")

    @pytest.mark.asyncio
    async def test_traversal_blocked_on_delete(self, storage):
        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await storage.delete("../../important")

    @pytest.mark.asyncio
    async def test_traversal_blocked_on_exists(self, storage):
        from app.core.exceptions import ValidationError

        with pytest.raises(ValidationError):
            await storage.exists("../../../etc/hosts")

    @pytest.mark.asyncio
    async def test_leading_slash_stripped(self, storage, tmp_path):
        # Leading slashes should be stripped and treated as relative
        await storage.save("/sources/file.txt", b"ok")
        assert (tmp_path / "sources" / "file.txt").exists()


# ─── factory ──────────────────────────────────────────────────────


class TestFactory:
    def test_get_storage_returns_local(self, monkeypatch):
        monkeypatch.setattr("app.services.storage.settings.STORAGE_BACKEND", "local")
        backend = get_storage()
        assert isinstance(backend, LocalStorage)

    def test_get_storage_singleton(self, monkeypatch):
        monkeypatch.setattr("app.services.storage.settings.STORAGE_BACKEND", "local")
        a = get_storage()
        b = get_storage()
        assert a is b

    def test_get_storage_s3_not_implemented(self, monkeypatch):
        monkeypatch.setattr("app.services.storage.settings.STORAGE_BACKEND", "s3")
        with pytest.raises(NotImplementedError, match="TASK-177"):
            get_storage()

    def test_get_storage_unknown_raises(self, monkeypatch):
        monkeypatch.setattr("app.services.storage.settings.STORAGE_BACKEND", "gcs")
        with pytest.raises(ValueError, match="Unknown STORAGE_BACKEND"):
            get_storage()

    def test_reset_storage_clears_singleton(self, monkeypatch):
        monkeypatch.setattr("app.services.storage.settings.STORAGE_BACKEND", "local")
        a = get_storage()
        reset_storage()
        b = get_storage()
        assert a is not b
