"""
YouTube parser — extracts transcript text from YouTube videos.

Parses the video ID from standard YouTube URL formats and retrieves the
transcript using a dual-strategy approach:
  1. Primary: ``yt-dlp`` — more resilient against YouTube endpoint changes
  2. Fallback: ``youtube_transcript_api`` — lighter, with retry + error handling

Auto-detects language with fallback to any available transcript.
"""

from __future__ import annotations

import asyncio
import json
import re
import shutil
import subprocess
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.core.constants import SourceType
from app.core.exceptions import ValidationError
from app.core.logging import logger
from app.services.parsers import BaseParser

# Regex patterns for YouTube video ID extraction.
_YOUTUBE_PATTERNS: list[re.Pattern[str]] = [
    # https://www.youtube.com/watch?v=VIDEO_ID
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/watch\?.*v=(?P<id>[a-zA-Z0-9_-]{11})"),
    # https://youtu.be/VIDEO_ID
    re.compile(r"(?:https?://)?youtu\.be/(?P<id>[a-zA-Z0-9_-]{11})"),
    # https://www.youtube.com/embed/VIDEO_ID
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/embed/(?P<id>[a-zA-Z0-9_-]{11})"),
    # https://www.youtube.com/v/VIDEO_ID
    re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/v/(?P<id>[a-zA-Z0-9_-]{11})"),
]

# Maximum retries for transcript fetch with youtube_transcript_api.
_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 2


def _extract_video_id(url: str) -> str:
    """Extract the 11-character video ID from a YouTube URL.

    Supports youtube.com/watch?v=, youtu.be/, youtube.com/embed/,
    and youtube.com/v/ formats.

    Args:
        url: A YouTube video URL.

    Returns:
        The 11-character video ID.

    Raises:
        ValidationError: If the video ID cannot be extracted.
    """
    # Try regex patterns first.
    for pattern in _YOUTUBE_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group("id")

    # Fallback: parse query string for 'v' parameter.
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    video_ids = qs.get("v", [])
    if video_ids and len(video_ids[0]) == 11:
        return video_ids[0]

    raise ValidationError(f"Could not extract YouTube video ID from URL: {url}")


def _format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS or MM:SS timestamp string."""
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class YoutubeParser(BaseParser):
    """Extract transcript text from YouTube videos.

    Uses a dual-strategy approach for resilience:
      1. ``yt-dlp`` (primary) — robust against YouTube endpoint changes
      2. ``youtube_transcript_api`` (fallback) — lighter, with retry logic

    Supports multiple URL formats.  Auto-detects transcript language
    with fallback to any available language if the preferred one is
    not available.
    """

    supported_types: set[SourceType] = {SourceType.YOUTUBE}

    async def parse(self, data: bytes, *, filename: str = "") -> str:
        """Extract transcript from a YouTube video URL.

        Args:
            data: The YouTube URL as UTF-8 encoded bytes.
            filename: Unused (kept for interface compatibility).

        Returns:
            Transcript text with timestamps.

        Raises:
            ValidationError: If the URL is invalid, the video ID cannot
                be extracted, or no transcript is available.
        """
        # Decode URL from bytes.
        try:
            url = data.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ValidationError("Invalid YouTube URL encoding.") from exc

        if not url:
            raise ValidationError("Empty YouTube URL provided.")

        logger.info("youtube_parse_start", url=url)

        # Extract video ID.
        video_id = _extract_video_id(url)
        logger.debug("youtube_video_id_extracted", video_id=video_id)

        # Strategy 1: Try yt-dlp (more resilient)
        transcript_segments = await self._fetch_via_ytdlp(video_id)

        # Strategy 2: Fallback to youtube_transcript_api with retries
        if transcript_segments is None:
            logger.info(
                "youtube_ytdlp_fallback",
                video_id=video_id,
                msg="yt-dlp failed or unavailable, falling back to youtube_transcript_api",
            )
            transcript_segments = await self._fetch_via_transcript_api(video_id)

        # Format segments with timestamps.
        lines: list[str] = []
        for segment in transcript_segments:
            raw_start = segment.get("start")
            start = float(raw_start) if isinstance(raw_start, (int, float)) else 0.0
            text = str(segment.get("text") or "").strip()
            if text:
                timestamp = _format_timestamp(start)
                lines.append(f"[{timestamp}] {text}")

        if not lines:
            raise ValidationError(f"Transcript for video '{video_id}' contains no text.")

        result = "\n".join(lines)
        logger.info(
            "youtube_parse_complete",
            video_id=video_id,
            segments=len(lines),
            length=len(result),
        )
        return result

    # ─── Strategy 1: yt-dlp ──────────────────────────────────────

    async def _fetch_via_ytdlp(
        self,
        video_id: str,
    ) -> list[dict[str, object]] | None:
        """Fetch transcript using yt-dlp subprocess.

        yt-dlp is more resilient against YouTube's endpoint changes and
        IP-based blocking compared to youtube_transcript_api.

        Returns:
            List of segment dicts, or None if yt-dlp is unavailable or fails.
        """
        if not shutil.which("yt-dlp"):
            logger.debug("youtube_ytdlp_not_installed")
            return None

        url = f"https://www.youtube.com/watch?v={video_id}"

        # yt-dlp can write subtitles to stdout as JSON.
        cmd = [
            "yt-dlp",
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            "en.*,en",
            "--sub-format",
            "json3",
            "--dump-json",
            url,
        ]

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60,
                ),
            )

            if result.returncode != 0:
                logger.warning(
                    "youtube_ytdlp_failed",
                    video_id=video_id,
                    stderr=result.stderr[:500] if result.stderr else "",
                )
                return None

            # Parse the JSON output to find subtitle info.
            info = json.loads(result.stdout)

            # Try to get subtitles from the info dict.
            segments = self._extract_segments_from_ytdlp(info, video_id)
            if segments:
                logger.info(
                    "youtube_ytdlp_success",
                    video_id=video_id,
                    segments=len(segments),
                )
                return segments

            # If no inline subtitles, try downloading the subtitle file directly.
            return await self._download_subs_via_ytdlp(video_id)

        except subprocess.TimeoutExpired:
            logger.warning("youtube_ytdlp_timeout", video_id=video_id)
            return None
        except Exception as exc:
            logger.warning(
                "youtube_ytdlp_error",
                video_id=video_id,
                error=str(exc),
            )
            return None

    def _extract_segments_from_ytdlp(
        self,
        info: dict[str, Any],
        video_id: str,
    ) -> list[dict[str, object]] | None:
        """Extract subtitle segments from yt-dlp JSON info dict."""
        # Check for subtitles or automatic_captions in the info.
        for key in ("subtitles", "automatic_captions"):
            subs = info.get(key, {})
            # Prefer English variants.
            for lang in ("en", "en-US", "en-GB", "en-orig"):
                if lang in subs:
                    for fmt in subs[lang]:
                        if fmt.get("ext") == "json3" and "url" in fmt:
                            # We'd need to download this URL — handled by fallback.
                            return None
            # Try any available language.
            if subs:
                first_lang = next(iter(subs))
                for fmt in subs[first_lang]:
                    if fmt.get("ext") == "json3" and "url" in fmt:
                        return None
        return None

    async def _download_subs_via_ytdlp(
        self,
        video_id: str,
    ) -> list[dict[str, object]] | None:
        """Download subtitle file directly via yt-dlp to a temp location."""
        import os
        import tempfile

        url = f"https://www.youtube.com/watch?v={video_id}"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_template = os.path.join(tmpdir, "%(id)s")
            cmd = [
                "yt-dlp",
                "--skip-download",
                "--write-subs",
                "--write-auto-subs",
                "--sub-langs",
                "en.*,en",
                "--sub-format",
                "json3",
                "-o",
                output_template,
                url,
            ]

            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=60,
                    ),
                )

                if result.returncode != 0:
                    logger.warning(
                        "youtube_ytdlp_sub_download_failed",
                        video_id=video_id,
                        stderr=result.stderr[:500] if result.stderr else "",
                    )
                    return None

                # Look for the downloaded subtitle file.
                for fname in os.listdir(tmpdir):
                    if fname.endswith(".json3"):
                        fpath = os.path.join(tmpdir, fname)
                        with open(fpath) as f:
                            sub_data = json.load(f)
                        return self._parse_json3_subtitles(sub_data)

                # Also try .vtt or .srt formats as fallback.
                for fname in os.listdir(tmpdir):
                    if fname.endswith((".vtt", ".srt")):
                        fpath = os.path.join(tmpdir, fname)
                        with open(fpath) as f:
                            content = f.read()
                        return self._parse_vtt_subtitles(content)

            except Exception as exc:
                logger.warning(
                    "youtube_ytdlp_sub_error",
                    video_id=video_id,
                    error=str(exc),
                )

        return None

    def _parse_json3_subtitles(
        self,
        data: dict[str, Any],
    ) -> list[dict[str, object]]:
        """Parse yt-dlp json3 subtitle format into segment dicts."""
        segments: list[dict[str, object]] = []
        events = data.get("events", [])

        for event in events:
            # Skip events without text segments.
            segs = event.get("segs")
            if not segs:
                continue

            start_ms = event.get("tStartMs", 0)
            duration_ms = event.get("dDurationMs", 0)
            text_parts = [s.get("utf8", "") for s in segs if s.get("utf8")]
            text = "".join(text_parts).strip()

            if text and text != "\n":
                segments.append(
                    {
                        "start": start_ms / 1000.0,
                        "duration": duration_ms / 1000.0,
                        "text": text,
                    }
                )

        return segments

    def _parse_vtt_subtitles(
        self,
        content: str,
    ) -> list[dict[str, object]]:
        """Parse WebVTT subtitle content into segment dicts."""
        segments: list[dict[str, object]] = []
        # Simple VTT parser: look for timestamp lines.
        timestamp_pattern = re.compile(
            r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
        )

        lines = content.split("\n")
        i = 0
        while i < len(lines):
            match = timestamp_pattern.match(lines[i])
            if match:
                h, m, s, ms = (
                    int(match.group(1)),
                    int(match.group(2)),
                    int(match.group(3)),
                    int(match.group(4)),
                )
                start = h * 3600 + m * 60 + s + ms / 1000.0

                h2, m2, s2, ms2 = (
                    int(match.group(5)),
                    int(match.group(6)),
                    int(match.group(7)),
                    int(match.group(8)),
                )
                end = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000.0

                # Collect text lines until empty line.
                i += 1
                text_lines = []
                while i < len(lines) and lines[i].strip():
                    # Strip VTT tags like <c>, </c>, etc.
                    cleaned = re.sub(r"<[^>]+>", "", lines[i]).strip()
                    if cleaned:
                        text_lines.append(cleaned)
                    i += 1

                text = " ".join(text_lines)
                if text:
                    segments.append(
                        {
                            "start": start,
                            "duration": end - start,
                            "text": text,
                        }
                    )
            i += 1

        return segments

    # ─── Strategy 2: youtube_transcript_api (fallback) ────────────

    async def _fetch_via_transcript_api(
        self,
        video_id: str,
    ) -> list[dict[str, object]]:
        """Fetch transcript via youtube_transcript_api with retry logic.

        Retries on transient XML parsing errors (empty response from YouTube)
        and other recoverable failures.

        Args:
            video_id: The 11-character YouTube video ID.

        Returns:
            List of transcript segment dicts.

        Raises:
            ValidationError: If all retries are exhausted.
        """
        from youtube_transcript_api import YouTubeTranscriptApi

        last_error: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                transcript = self._find_best_transcript(video_id)
                segments = transcript.fetch()

                logger.info(
                    "youtube_transcript_api_success",
                    video_id=video_id,
                    language=transcript.language_code,
                    segments=len(segments),
                    attempt=attempt,
                )
                return list(segments)

            except Exception as exc:
                last_error = exc
                error_msg = str(exc)

                # Detect transient XML errors (empty response from YouTube).
                is_transient = any(
                    marker in error_msg
                    for marker in (
                        "no element found",
                        "ParseError",
                        "ExpatError",
                        "not well-formed",
                    )
                )

                if is_transient and attempt < _MAX_RETRIES:
                    delay = _RETRY_DELAY_SECONDS * attempt
                    logger.warning(
                        "youtube_transcript_api_retry",
                        video_id=video_id,
                        attempt=attempt,
                        max_retries=_MAX_RETRIES,
                        delay=delay,
                        error=error_msg[:200],
                    )
                    await asyncio.sleep(delay)
                    continue

                # Non-transient error or final attempt — break out.
                break

        # All strategies exhausted.
        logger.error(
            "youtube_transcript_all_failed",
            video_id=video_id,
            error=str(last_error),
        )
        raise ValidationError(
            f"Could not fetch transcript for YouTube video '{video_id}'. "
            f"This may be due to YouTube blocking the request, the video "
            f"having no captions, or a temporary network issue. "
            f"Last error: {last_error}"
        ) from last_error

    def _find_best_transcript(self, video_id: str):
        """Find the best available transcript for a video.

        Priority: manual English > generated English > any language.

        Returns:
            A transcript object from youtube_transcript_api.

        Raises:
            ValidationError: If no transcript is found at all.
        """
        from youtube_transcript_api import YouTubeTranscriptApi

        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        except Exception as exc:
            raise ValidationError(
                f"No transcript available for YouTube video '{video_id}': {exc}"
            ) from exc

        # Try manually created English transcript.
        try:
            return transcript_list.find_manually_created_transcript(["en", "en-US", "en-GB"])
        except Exception:
            logger.debug("youtube_no_manual_transcript", video_id=video_id)

        # Try auto-generated English transcript.
        try:
            return transcript_list.find_generated_transcript(["en", "en-US", "en-GB"])
        except Exception:
            logger.debug("youtube_no_generated_en_transcript", video_id=video_id)

        # Fall back to any available transcript.
        try:
            available = list(transcript_list)
            if available:
                return available[0]
        except Exception:
            pass

        raise ValidationError(
            f"No transcript found for YouTube video '{video_id}'. "
            "The video may not have captions enabled."
        )
