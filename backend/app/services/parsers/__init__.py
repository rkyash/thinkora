"""
Parser factory — dispatches to the correct parser based on SourceType.

Usage:
    from app.services.parsers import dispatch_parser
    from app.core.constants import SourceType

    parser = dispatch_parser(SourceType.PDF)
    text = await parser.parse(file_bytes, filename="doc.pdf")

Each parser module implements the ``BaseParser`` protocol:
  - ``parse(data, *, filename) -> str``  — extracts text from raw bytes
  - ``supported_types -> set[SourceType]`` — which source types it handles
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.core.logging import logger

if TYPE_CHECKING:
    pass


# ─── Base Parser ──────────────────────────────────────────────────


class BaseParser(ABC):
    """Abstract base class for all document parsers.

    Subclasses must implement:
      - ``parse(data, *, filename)`` — extract text from raw bytes
      - ``supported_types`` — class-level set of SourceType values this parser handles
    """

    supported_types: set[SourceType] = set()

    @abstractmethod
    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """
        Parse raw file bytes and return extracted plain text.

        Args:
            data: Raw file content as bytes.
            filename: Original filename (used for logging and format hints).

        Returns:
            Extracted text content as a single string.

        Raises:
            ValidationError: If the file is corrupt, too large, or unparseable.
        """
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} types={self.supported_types}>"


# ─── Parser Registry ─────────────────────────────────────────────

# Lazy-loaded parser instances, keyed by SourceType.
# Populated on first call to dispatch_parser().
_registry: dict[SourceType, BaseParser] | None = None


def _build_registry() -> dict[SourceType, BaseParser]:
    """
    Import all parser modules and build the SourceType → parser mapping.

    Uses lazy imports so parser-specific heavy dependencies (pymupdf, pandas,
    etc.) are only loaded when actually needed.
    """
    registry: dict[SourceType, BaseParser] = {}

    # Each entry: (module_path, class_name)
    # Parsers are imported lazily to avoid pulling in heavy libs at startup.
    parser_specs: list[tuple[str, str]] = [
        ("app.services.parsers.pdf", "PdfParser"),
        ("app.services.parsers.docx", "DocxParser"),
        ("app.services.parsers.xlsx", "XlsxParser"),
        ("app.services.parsers.csv", "CsvParser"),
        ("app.services.parsers.markdown", "MarkdownParser"),
        ("app.services.parsers.txt", "TxtParser"),
        ("app.services.parsers.pptx", "PptxParser"),
        ("app.services.parsers.epub", "EpubParser"),
        ("app.services.parsers.url", "UrlParser"),
        ("app.services.parsers.youtube", "YoutubeParser"),
        ("app.services.parsers.audio", "AudioParser"),
        ("app.services.parsers.image", "ImageParser"),
    ]

    for module_path, class_name in parser_specs:
        try:
            import importlib

            module = importlib.import_module(module_path)
            parser_cls = getattr(module, class_name)
            parser_instance = parser_cls()

            for source_type in parser_instance.supported_types:
                if source_type in registry:
                    logger.warning(
                        "parser_registry_conflict",
                        source_type=source_type.value,
                        existing=repr(registry[source_type]),
                        new=repr(parser_instance),
                    )
                registry[source_type] = parser_instance

            logger.debug(
                "parser_registered",
                parser=class_name,
                types=[t.value for t in parser_instance.supported_types],
            )
        except ImportError as exc:
            # Parser module or its dependency not installed — skip gracefully.
            # This allows the app to start even if some parser libs are missing.
            logger.warning(
                "parser_import_skipped",
                module=module_path,
                class_name=class_name,
                error=str(exc),
            )
        except Exception as exc:
            logger.error(
                "parser_registration_failed",
                module=module_path,
                class_name=class_name,
                error=str(exc),
            )

    return registry


def _get_registry() -> dict[SourceType, BaseParser]:
    """Return the parser registry, building it on first access."""
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = _build_registry()
    return _registry


# ─── Public API ───────────────────────────────────────────────────


def dispatch_parser(source_type: SourceType) -> BaseParser:
    """
    Return the parser instance for the given source type.

    Args:
        source_type: The type of source document to parse.

    Returns:
        A ``BaseParser`` subclass instance capable of parsing the source type.

    Raises:
        ValidationError: If no parser is registered for the source type.
    """
    registry = _get_registry()
    parser = registry.get(source_type)

    if parser is None:
        available = sorted(t.value for t in registry)
        raise ValidationError(
            f"No parser available for source type '{source_type.value}'. "
            f"Supported types: {', '.join(available) or 'none'}"
        )

    logger.debug(
        "parser_dispatched",
        source_type=source_type.value,
        parser=repr(parser),
    )
    return parser


def get_supported_types() -> list[SourceType]:
    """Return a sorted list of all source types with registered parsers."""
    return sorted(_get_registry().keys(), key=lambda t: t.value)


def reset_registry() -> None:
    """Reset the parser registry. Used in tests to force re-registration."""
    global _registry  # noqa: PLW0603
    _registry = None
