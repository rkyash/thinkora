"""
Plain text parser.
"""

from __future__ import annotations

import chardet

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.services.parsers import BaseParser


class TxtParser(BaseParser):
    """Parser for plain text files (.txt)."""

    supported_types = {SourceType.TXT, SourceType.TEXT}

    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """
        Parse raw bytes as a text string.

        Attempts to detect encoding if UTF-8 fails.
        """
        if not data:
            return ""

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback to auto-detection
            detected = chardet.detect(data)
            encoding = detected.get("encoding") or "utf-8"
            try:
                text = data.decode(encoding, errors="replace")
            except Exception as exc:
                raise ValidationError(f"Failed to decode text file: {exc}") from exc

        return text.strip()
