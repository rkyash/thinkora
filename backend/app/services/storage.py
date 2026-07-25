"""
File storage abstraction — Protocol-based backend with local filesystem implementation.

Active backend is selected by the STORAGE_BACKEND setting:
  - "local"  → LocalStorage (default, stores under ~/.thinkora/)
  - "s3"     → S3Storage (future: TASK-177)
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Protocol, runtime_checkable

import aiofiles
import aiofiles.os

from app.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import logger

# ─── Storage Protocol ────────────────────────────────────────────────


@runtime_checkable
class StorageBackend(Protocol):
    """Abstract storage interface. Any backend must implement these four methods."""

    async def save(self, path: str, data: bytes) -> str:
        """
        Persist *data* at *path* (relative to the storage root).

        Returns:
            The normalized path where the file was saved.
        """
        ...

    async def load(self, path: str) -> bytes:
        """
        Retrieve the contents of the file at *path*.

        Raises:
            NotFoundError: if the file does not exist.
        """
        ...

    async def delete(self, path: str) -> None:
        """
        Remove the file at *path*.

        This is a no-op if the file does not exist (idempotent delete).
        """
        ...

    async def exists(self, path: str) -> bool:
        """Return True if *path* exists in storage."""
        ...


# ─── Local Filesystem Backend ────────────────────────────────────────


class LocalStorage:
    """
    Stores files on the local filesystem under ``settings.data_dir``.

    Directory structure::

        ~/.thinkora/
        ├── sources/          ← uploaded source files
        ├── exports/          ← generated exports (zip / PDF)
        ├── audio/            ← generated podcast audio
        └── ...
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or settings.data_dir

    @property
    def root(self) -> Path:
        """Resolved root directory for local storage."""
        return self._root

    # ── helpers ───────────────────────────────────────────────

    def _resolve(self, path: str) -> Path:
        """
        Resolve a relative *path* against the storage root.

        Raises:
            ValidationError: if the path attempts directory traversal.
        """
        # Normalize and strip leading slashes so it's truly relative
        clean = Path(path.lstrip("/"))
        resolved = (self._root / clean).resolve()

        # Guard against traversal (e.g. "../../etc/passwd")
        if not str(resolved).startswith(str(self._root.resolve())):
            raise ValidationError(f"Path traversal detected: {path}")

        return resolved

    # ── public API ────────────────────────────────────────────

    async def save(self, path: str, data: bytes) -> str:
        """Save *data* to the local filesystem at *path*."""
        target = self._resolve(path)

        # Ensure parent directories exist
        await aiofiles.os.makedirs(target.parent, exist_ok=True)

        async with aiofiles.open(target, "wb") as fh:
            await fh.write(data)

        logger.info(
            "storage_save",
            backend="local",
            path=str(path),
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest()[:16],
        )
        return str(path)

    async def load(self, path: str) -> bytes:
        """Load and return file contents from *path*."""
        target = self._resolve(path)

        if not target.is_file():
            raise NotFoundError("File", str(path))

        async with aiofiles.open(target, "rb") as fh:
            data = await fh.read()

        logger.debug(
            "storage_load",
            backend="local",
            path=str(path),
            size_bytes=len(data),
        )
        return data

    async def delete(self, path: str) -> None:
        """Delete the file at *path*. No-op if it doesn't exist."""
        target = self._resolve(path)

        if target.is_file():
            await aiofiles.os.remove(target)
            logger.info("storage_delete", backend="local", path=str(path))

            # Clean up empty parent directories up to the root
            parent = target.parent
            while parent != self._root.resolve() and parent != parent.parent:
                try:
                    await aiofiles.os.rmdir(parent)
                    logger.debug(
                        "storage_rmdir_empty",
                        backend="local",
                        directory=str(parent),
                    )
                    parent = parent.parent
                except OSError:
                    break  # Directory not empty — stop climbing

    async def exists(self, path: str) -> bool:
        """Return True if the file at *path* exists."""
        target = self._resolve(path)
        return target.is_file()

    async def list_dir(self, prefix: str = "") -> list[str]:
        """
        List all files under *prefix* (relative to root).

        Returns a list of relative paths (POSIX-style) under the prefix.
        Useful for enumerating exports, audio files, etc.
        """
        target = self._resolve(prefix) if prefix else self._root
        if not target.is_dir():
            return []

        results: list[str] = []
        for item in target.rglob("*"):
            if item.is_file():
                rel = item.relative_to(self._root)
                results.append(str(rel))

        return sorted(results)

    async def size(self, path: str) -> int:
        """Return the size of the file at *path* in bytes."""
        target = self._resolve(path)
        if not target.is_file():
            raise NotFoundError("File", str(path))
        stat = await aiofiles.os.stat(target)
        return stat.st_size


# ─── Factory ─────────────────────────────────────────────────────────


_backend_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """
    Return the active storage backend (singleton).

    Backend is selected by ``settings.STORAGE_BACKEND``:
      - ``"local"`` → :class:`LocalStorage`
      - ``"s3"``    → raises ``NotImplementedError`` (TASK-177)
    """
    global _backend_instance  # noqa: PLW0603

    if _backend_instance is not None:
        return _backend_instance

    backend = settings.STORAGE_BACKEND.lower()

    if backend == "local":
        _backend_instance = LocalStorage()
        logger.info(
            "storage_backend_initialized",
            backend="local",
            root=str(settings.data_dir),
        )
    elif backend == "s3":
        raise NotImplementedError(
            "S3 storage backend is not yet implemented (see TASK-177). "
            "Set STORAGE_BACKEND=local in your .env file."
        )
    else:
        raise ValueError(
            f"Unknown STORAGE_BACKEND: '{backend}'. "
            f"Supported values: 'local', 's3'."
        )

    return _backend_instance


def reset_storage() -> None:
    """
    Reset the cached storage backend singleton.

    Primarily used in tests to swap backends between test cases.
    """
    global _backend_instance  # noqa: PLW0603
    _backend_instance = None
