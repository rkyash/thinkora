"""
Markdown / plain-text parser — decodes raw bytes to text.

Markdown and plain text are already human-readable, so this parser does
minimal processing: just encoding detection and decoding.
"""

from __future__ import annotations

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.core.logging import logger
from app.services.parsers import BaseParser


class MarkdownParser(BaseParser):
    """Extract text from Markdown and plain-text files."""

    supported_types: set[SourceType] = {SourceType.MARKDOWN, SourceType.TXT, SourceType.TEXT}

    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """Decode raw bytes and return the text content unchanged.

        Args:
            data: Raw file content.
            filename: Original filename (used for logging).

        Returns:
            Decoded text string with structure preserved.

        Raises:
            ValidationError: If the file cannot be decoded.
        """
        logger.info("markdown_parse_start", filename=filename, size=len(data))

        if not data:
            logger.warning("markdown_empty", filename=filename)
            return ""

        text = self._decode(data, filename=filename)

        logger.info(
            "markdown_parse_complete",
            filename=filename,
            length=len(text),
        )
        return text

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _decode(data: bytes, *, filename: str) -> str:
        """Decode bytes to string, trying utf-8 first then latin-1."""
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            logger.debug(
                "markdown_utf8_fallback",
                filename=filename,
                msg="utf-8 decode failed, falling back to latin-1",
            )
            try:
                return data.decode("latin-1")
            except UnicodeDecodeError as exc:
                raise ValidationError(f"Cannot decode file '{filename}': {exc}") from exc
