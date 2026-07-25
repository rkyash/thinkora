"""
EPUB parser — extracts chapter text from EPUB files.

Uses ``ebooklib`` for EPUB reading and ``BeautifulSoup`` for HTML stripping.
Each chapter is emitted as a heading + content block.
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from ebooklib import epub

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.core.logging import logger
from app.services.parsers import BaseParser


class EpubParser(BaseParser):
    """Parse EPUB e-book files into plain text.

    Each chapter/document item in the EPUB spine is extracted as a
    heading (from the first ``<h1>``–``<h6>`` tag, or a fallback title)
    followed by the body text with all HTML tags stripped.
    """

    supported_types: set[SourceType] = {SourceType.EPUB}

    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """Extract text from an EPUB file.

        Args:
            data: Raw EPUB file bytes.
            filename: Original filename (used for logging).

        Returns:
            Extracted chapter text as a single string.

        Raises:
            ValidationError: If the EPUB cannot be read or contains no text.
        """
        logger.info("epub_parse_start", filename=filename, size=len(data))

        try:
            book = epub.read_epub(
                "book.epub",
                options={"ignore_ncx": True},
                stream=data,
            )
        except Exception as exc:
            logger.error("epub_read_failed", filename=filename, error=str(exc))
            raise ValidationError(f"Failed to read EPUB file '{filename}': {exc}") from exc

        chapters: list[str] = []
        chapter_index = 0

        for item in book.get_items_of_type(epub.EpubHtml.ITEM_DOCUMENT):
            html_content = item.get_content()
            soup = BeautifulSoup(html_content, "html.parser")

            # Try to extract a heading from the first h1–h6 tag.
            heading_tag = soup.find(["h1", "h2", "h3", "h4", "h5", "h6"])
            if heading_tag:
                heading = heading_tag.get_text(strip=True)
                # Remove heading from soup to avoid duplication in body.
                heading_tag.decompose()
            else:
                chapter_index += 1
                heading = f"Chapter {chapter_index}"

            # Strip remaining HTML and get clean text.
            body_text = soup.get_text(separator="\n", strip=True)

            if not body_text.strip():
                continue

            chapters.append(f"# {heading}\n\n{body_text}")

        if not chapters:
            logger.warning("epub_no_content", filename=filename)
            raise ValidationError(f"EPUB file '{filename}' contains no extractable text content.")

        result = "\n\n---\n\n".join(chapters)
        logger.info(
            "epub_parse_complete",
            filename=filename,
            chapters=len(chapters),
            length=len(result),
        )
        return result
