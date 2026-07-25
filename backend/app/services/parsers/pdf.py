"""
PDF parser — extracts text from PDF files using PyMuPDF (fitz).

Preserves paragraph structure via layout-aware extraction and logs
page/character counts for observability.
"""

from __future__ import annotations

import io

import fitz  # pymupdf

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.core.logging import logger
from app.services.parsers import BaseParser

# 100 MB limit
_MAX_PDF_SIZE_BYTES: int = 100 * 1024 * 1024


class PdfParser(BaseParser):
    """Extract text from PDF documents using PyMuPDF."""

    supported_types: set[SourceType] = {SourceType.PDF}

    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """Parse raw PDF bytes and return extracted plain text.

        Args:
            data: Raw PDF file content.
            filename: Original filename (used for logging).

        Returns:
            Extracted text with paragraph structure preserved.

        Raises:
            ValidationError: If the file exceeds 100 MB or cannot be parsed.
        """
        file_size = len(data)

        if file_size > _MAX_PDF_SIZE_BYTES:
            max_mb = _MAX_PDF_SIZE_BYTES // (1024 * 1024)
            raise ValidationError(
                f"PDF file exceeds maximum size of {max_mb}MB "
                f"(got {file_size / (1024 * 1024):.1f}MB)"
            )

        logger.info(
            "pdf_parse_start",
            filename=filename,
            file_size_bytes=file_size,
        )

        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise ValidationError(
                f"Failed to open PDF file '{filename}': {exc}"
            ) from exc

        pages: list[str] = []
        try:
            for page_num, page in enumerate(doc, start=1):
                # Use "text" extraction with sort=True for reading-order layout
                page_text = page.get_text("text", sort=True)
                if page_text.strip():
                    pages.append(page_text.strip())
        except Exception as exc:
            raise ValidationError(
                f"Failed to extract text from PDF '{filename}' "
                f"at page {page_num}: {exc}"
            ) from exc
        finally:
            doc.close()

        text = "\n\n".join(pages)

        logger.info(
            "pdf_parse_complete",
            filename=filename,
            page_count=len(pages),
            char_count=len(text),
        )

        return text
