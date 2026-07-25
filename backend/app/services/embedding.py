"""
Embedding service — sentence-transformers singleton with lazy loading.

Wraps a sentence-transformers model behind a thread-safe singleton so the
model is loaded exactly once (on first use) and shared across all callers.

Usage:
    from app.services.embedding import get_embedding_service

    svc = get_embedding_service()
    vectors = svc.embed_texts(["hello world", "foo bar"])
    query_vec = svc.embed_query("search term")
    dim = svc.get_dimension()
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from app.config import settings
from app.core.logging import logger

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Thread-safe, lazily-initialized sentence-transformers wrapper.

    The model is loaded on the first call to any public method and kept alive
    for the lifetime of the process.  A ``threading.Lock`` guards the loading
    step so concurrent threads never trigger a double-load.
    """

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL,
        device: str = settings.EMBEDDING_DEVICE,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._model: SentenceTransformer | None = None
        self._lock = threading.Lock()

    # ── internal ──────────────────────────────────────────────

    def _ensure_model(self) -> SentenceTransformer:
        """Load the model if it hasn't been loaded yet (double-checked locking)."""
        if self._model is not None:
            return self._model

        with self._lock:
            # Re-check after acquiring the lock (another thread may have loaded it)
            if self._model is not None:
                return self._model

            logger.info(
                "embedding_model_loading",
                model=self._model_name,
                device=self._device,
            )

            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self._model_name,
                device=self._device,
            )

            logger.info(
                "embedding_model_loaded",
                model=self._model_name,
                device=self._device,
                dimension=self._model.get_sentence_embedding_dimension(),
            )

        return self._model

    # ── public API ────────────────────────────────────────────

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch-encode a list of texts into embedding vectors.

        Args:
            texts: Plain-text strings to embed.

        Returns:
            A list of float vectors, one per input text.
        """
        if not texts:
            return []

        model = self._ensure_model()
        embeddings = model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        logger.debug("embed_texts", count=len(texts))
        return embeddings.tolist()  # type: ignore[no-any-return]

    def embed_query(self, query: str) -> list[float]:
        """Encode a single search query.

        Some models support a ``prompt_name`` kwarg for asymmetric retrieval;
        if the loaded model exposes one, we pass ``"query"`` so the model
        prepends the appropriate instruction prefix automatically.

        Args:
            query: The search query string.

        Returns:
            A single float vector.
        """
        model = self._ensure_model()

        # Attempt to use prompt_name for models that support asymmetric search
        # (e.g. INSTRUCTOR, E5).  Falls back silently for models that don't.
        encode_kwargs: dict[str, object] = {
            "show_progress_bar": False,
            "convert_to_numpy": True,
        }

        # Check if model supports prompt_name (e.g. sentence-transformers >= 2.3)
        try:
            embedding = model.encode(
                query,
                prompt_name="query",
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        except (TypeError, ValueError):
            # Model doesn't support prompt_name — encode without it
            embedding = model.encode(
                query,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

        logger.debug("embed_query", query_len=len(query))
        return embedding.tolist()  # type: ignore[no-any-return]

    def get_dimension(self) -> int:
        """Return the embedding vector dimension for the loaded model.

        Returns:
            Integer dimension (e.g. 384 for ``all-MiniLM-L6-v2``).
        """
        model = self._ensure_model()
        dim = model.get_sentence_embedding_dimension()
        if dim is None:
            raise RuntimeError(
                f"Could not determine embedding dimension for model '{self._model_name}'"
            )
        return int(dim)


# ─── Singleton Instance & Factory ─────────────────────────────────────

_instance: EmbeddingService | None = None
_factory_lock = threading.Lock()


def get_embedding_service() -> EmbeddingService:
    """Return the module-level ``EmbeddingService`` singleton.

    The instance is created on first call; the underlying model is loaded
    lazily on first encode.
    """
    global _instance  # noqa: PLW0603

    if _instance is not None:
        return _instance

    with _factory_lock:
        if _instance is not None:
            return _instance
        _instance = EmbeddingService()
        logger.info(
            "embedding_service_created",
            model=settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE,
        )

    return _instance


def reset_embedding_service() -> None:
    """Reset the singleton (for testing)."""
    global _instance  # noqa: PLW0603
    _instance = None
