"""
CSV parser — converts CSV files into markdown table text.

Uses pandas for robust CSV handling with encoding fallback (utf-8 → latin-1).
Only the first 1 000 rows are parsed to keep downstream token costs bounded.
"""

from __future__ import annotations

import io

import pandas as pd

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.core.logging import logger
from app.services.parsers import BaseParser

# Maximum rows to parse from a CSV file.
_MAX_ROWS = 1_000


class CsvParser(BaseParser):
    """Extract text from CSV files as a markdown-formatted table."""

    supported_types: set[SourceType] = {SourceType.CSV}

    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """Parse raw CSV bytes and return a markdown table string.

        Args:
            data: Raw CSV file content.
            filename: Original filename (used for logging).

        Returns:
            Markdown-formatted table of the first *_MAX_ROWS* rows.

        Raises:
            ValidationError: If the CSV cannot be decoded or parsed.
        """
        logger.info("csv_parse_start", filename=filename, size=len(data))

        # --- Decode with fallback -------------------------------------------
        decoded = self._decode(data, filename=filename)

        # --- Read into DataFrame -------------------------------------------
        try:
            df = pd.read_csv(
                io.StringIO(decoded),
                nrows=_MAX_ROWS,
                on_bad_lines="skip",
            )
        except Exception as exc:
            logger.error("csv_read_failed", filename=filename, error=str(exc))
            raise ValidationError(
                f"Failed to parse CSV file '{filename}': {exc}"
            ) from exc

        if df.empty:
            logger.warning("csv_empty", filename=filename)
            return ""

        # --- Convert to markdown table --------------------------------------
        text = df.to_markdown(index=False)

        logger.info(
            "csv_parse_complete",
            filename=filename,
            rows=len(df),
            columns=len(df.columns),
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
                "csv_utf8_fallback",
                filename=filename,
                msg="utf-8 decode failed, falling back to latin-1",
            )
            try:
                return data.decode("latin-1")
            except UnicodeDecodeError as exc:
                raise ValidationError(
                    f"Cannot decode CSV file '{filename}': {exc}"
                ) from exc
