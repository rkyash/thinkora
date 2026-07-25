"""
Audio Service — Generates multi-speaker podcast audio from notebook content.
"""

from __future__ import annotations

import asyncio
import io
import json
import re
from typing import Any

import structlog
from gtts import gTTS
from pydub import AudioSegment
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging import logger
from app.core.prompt_security import sanitize_user_content
from app.repositories import chunk_repo
from app.services.llm import get_llm_service
from app.services.notification import publish_event
from app.services.storage import get_storage

log: structlog.BoundLogger = structlog.get_logger(__name__)

_PODCAST_PROMPT = """\
You are an expert podcast scriptwriter. Create an engaging, conversational podcast script \
based on the provided source material.

There are exactly two speakers:
- "Host": Asks questions, guides the conversation, and represents the curious learner.
- "Expert": Explains the concepts clearly with analogies and deep knowledge.

Output ONLY a valid JSON array of speech segments. No markdown fences, no explanation.
[
  {{"speaker": "Host", "text": "Welcome everyone! Today we're diving into..."}},
  {{"speaker": "Expert", "text": "Thanks for having me. This topic is fascinating because..."}}
]

Rules:
- Keep the tone conversational, engaging, and educational.
- The podcast should be concise but informative (around 10-15 exchanges).
- Do not use sound effects or stage directions in the text.
- Ensure the JSON is perfectly formatted.

Source material:
{content}
"""


def _extract_json(text: str) -> Any:
    """Extract and parse the first JSON array or object from LLM output."""
    text = re.sub(r"```(?:json)?\s*", "", text)
    text = text.strip().rstrip("`").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from LLM output: {text[:200]}")


async def _collect_notebook_text(db: AsyncSession, notebook_id: str, max_chars: int = 60_000) -> str:
    """Aggregate document chunk text from a notebook (up to max_chars)."""
    chunks = await chunk_repo.list_all(db, notebook_id=notebook_id, limit=500)
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        if total >= max_chars:
            break
        text = chunk.content or ""
        parts.append(text)
        total += len(text)
    raw = "\n\n".join(parts)
    return sanitize_user_content(raw, max_chars=max_chars)


def _gtts_synthesize(text: str, is_host: bool) -> io.BytesIO:
    """Synthesize text to MP3 using gTTS. Runs synchronously."""
    # Use different TLDs to simulate different voices
    tld = "com" if is_host else "co.uk"
    tts = gTTS(text=text, lang="en", tld=tld, slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return fp


async def _elevenlabs_synthesize(text: str, is_host: bool) -> io.BytesIO:
    """Synthesize text to MP3 using ElevenLabs API (requires API key)."""
    import httpx
    
    api_key = settings.ELEVENLABS_API_KEY
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY not configured")

    # Hardcoded voice IDs for host and expert
    voice_id = "21m00Tcm4TlvDq8ikWAM" if is_host else "EXAVITQu4vr4xnSDxMaL"
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key,
    }
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers, timeout=30.0)
        response.raise_for_status()
        
    fp = io.BytesIO(response.content)
    fp.seek(0)
    return fp


class AudioService:
    """
    Service for generating podcast audio from notebook content.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._llm = get_llm_service()
        self._storage = get_storage()

    async def generate_podcast(
        self,
        notebook_id: str,
        generation_id: str,
        tts_backend: str = "gtts",
        model: str | None = None,
    ) -> str:
        """
        Generate a multi-speaker podcast from a notebook's content.
        
        Steps:
        1. Script generation via LLM.
        2. TTS conversion per segment.
        3. Audio stitching with pauses.
        4. Save to storage.
        
        Returns:
            The storage path of the final MP3.
        """
        channel_id = generation_id

        # 1. Fetch content
        await publish_event(channel_id, {"status": "processing", "step": "reading_content", "pct": 10})
        content = await _collect_notebook_text(self._db, notebook_id)
        if not content.strip():
            raise ValueError("No source content found in notebook.")

        # 2. Generate script
        await publish_event(channel_id, {"status": "processing", "step": "generating_script", "pct": 20})
        prompt = _PODCAST_PROMPT.format(content=content[:50_000])
        messages = [{"role": "user", "content": prompt}]

        log.info("generate_podcast_script_start", notebook_id=notebook_id)
        raw = await self._llm.get_chat_completion(messages=messages, model=model, temperature=0.7)
        
        try:
            script = _extract_json(raw)
        except ValueError as exc:
            log.error("podcast_script_parse_error", error=str(exc))
            raise

        if not isinstance(script, list) or not script:
            raise ValueError("LLM returned invalid script format.")

        # 3. TTS Conversion
        await publish_event(channel_id, {"status": "processing", "step": "synthesizing_audio", "pct": 40})
        
        audio_segments: list[AudioSegment] = []
        total_segments = len(script)
        last_tts_error: Exception | None = None
        
        for idx, segment in enumerate(script):
            speaker = segment.get("speaker", "Host")
            text = segment.get("text", "")
            if not text:
                continue
                
            is_host = (speaker.lower() == "host")
            
            # Synthesize
            try:
                if tts_backend == "elevenlabs" and settings.ELEVENLABS_API_KEY:
                    fp = await _elevenlabs_synthesize(text, is_host)
                else:
                    fp = await asyncio.to_thread(_gtts_synthesize, text, is_host)
                    
                # Load into pydub
                audio_seg = await asyncio.to_thread(AudioSegment.from_file, fp, format="mp3")
                audio_segments.append(audio_seg)
            except Exception as e:
                log.error("tts_generation_failed", error=str(e), text=text[:50])
                last_tts_error = e
                continue
                
            # Update progress incrementally
            pct = 40 + int(40 * (idx / total_segments))
            await publish_event(channel_id, {"status": "processing", "step": "synthesizing_audio", "pct": pct})

        if not audio_segments:
            err_suffix = f": {str(last_tts_error)}" if last_tts_error else ""
            raise ValueError(f"Failed to generate any audio segments{err_suffix}")

        # 4. Audio stitching
        await publish_event(channel_id, {"status": "processing", "step": "stitching_audio", "pct": 80})
        
        # 0.5 second pause between speakers
        pause = AudioSegment.silent(duration=500)
        
        final_audio = audio_segments[0]
        for seg in audio_segments[1:]:
            final_audio = final_audio + pause + seg
            
        # Export to BytesIO
        out_fp = io.BytesIO()
        await asyncio.to_thread(final_audio.export, out_fp, format="mp3")
        audio_bytes = out_fp.getvalue()

        # 5. Storage
        await publish_event(channel_id, {"status": "processing", "step": "saving", "pct": 95})
        path = f"audio/{generation_id}.mp3"
        saved_path = await self._storage.save(path, audio_bytes)
        
        await publish_event(channel_id, {"status": "ready", "step": "done", "pct": 100})
        log.info("generate_podcast_done", notebook_id=notebook_id, path=saved_path)
        
        return saved_path
