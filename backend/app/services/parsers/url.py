"""
URL parser — fetches a web page and extracts article text.

SSRF-guarded: validates the URL against internal/private networks before
fetching.  Uses ``readability-lxml`` for article extraction and
``BeautifulSoup`` for final HTML stripping.
"""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup
from readability import Document

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.core.logging import logger
from app.core.security import validate_url_ssrf
from app.services.parsers import BaseParser

# Maximum response body size: 10 MB.
_MAX_RESPONSE_BYTES = 10 * 1024 * 1024


class UrlParser(BaseParser):
    """Fetch a web page and extract its main article text.

    The parser validates the URL for SSRF attacks, fetches the page
    with a 30-second timeout, extracts the article using readability,
    and strips any remaining HTML with BeautifulSoup.
    """

    supported_types: set[SourceType] = {SourceType.URL}

    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """Fetch and extract text from a URL.

        Args:
            data: The URL as UTF-8 encoded bytes.
            filename: Unused for URL parsing (kept for interface compat).

        Returns:
            Extracted article text as a plain string.

        Raises:
            ValidationError: If the URL is invalid, unreachable, or
                the response exceeds the size limit.
        """
        # Decode URL from bytes.
        try:
            url = data.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValidationError("Invalid URL encoding.") from exc

        if not url:
            raise ValidationError("Empty URL provided.")

        logger.info("url_parse_start", url=url)

        # ── SSRF guard ────────────────────────────────────────────
        try:
            validated_url = validate_url_ssrf(url)
        except Exception as exc:
            logger.warning("url_ssrf_blocked", url=url, error=str(exc))
            raise ValidationError(f"URL blocked by security policy: {url}") from exc

        # ── Fetch page ────────────────────────────────────────────
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                max_redirects=5,
            ) as client:
                response = await client.get(validated_url)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.error("url_fetch_timeout", url=validated_url)
            raise ValidationError(f"Timed out fetching URL: {validated_url}") from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "url_fetch_http_error",
                url=validated_url,
                status=exc.response.status_code,
            )
            raise ValidationError(
                f"HTTP {exc.response.status_code} error fetching URL: {validated_url}"
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("url_fetch_failed", url=validated_url, error=str(exc))
            raise ValidationError(f"Failed to fetch URL: {validated_url}") from exc

        # ── Size check ────────────────────────────────────────────
        content_length = len(response.content)
        if content_length > _MAX_RESPONSE_BYTES:
            logger.warning(
                "url_response_too_large",
                url=validated_url,
                size=content_length,
                max=_MAX_RESPONSE_BYTES,
            )
            raise ValidationError(
                f"Response too large ({content_length // (1024 * 1024)}MB). "
                f"Maximum allowed: {_MAX_RESPONSE_BYTES // (1024 * 1024)}MB."
            )

        html = response.text
        if not html.strip():
            raise ValidationError(f"Empty response from URL: {validated_url}")

        # ── Extract article with readability ──────────────────────
        try:
            doc = Document(html)
            title = doc.title() or ""
            article_html = doc.summary()
        except Exception as exc:
            logger.error("url_readability_failed", url=validated_url, error=str(exc))
            raise ValidationError(f"Failed to extract article from URL: {validated_url}") from exc

        # ── Strip HTML with BeautifulSoup ─────────────────────────
        soup = BeautifulSoup(article_html, "html.parser")
        article_text = soup.get_text(separator="\n", strip=True)

        if not article_text.strip():
            raise ValidationError(f"No readable content found at URL: {validated_url}")

        # Prepend title if available.
        parts: list[str] = []
        if title.strip():
            parts.append(f"# {title.strip()}")
        parts.append(article_text)

        result = "\n\n".join(parts)
        logger.info(
            "url_parse_complete",
            url=validated_url,
            length=len(result),
        )
        return result
