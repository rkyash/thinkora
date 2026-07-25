"""
Prompt Security Utility — TASK-203

Provides safe prompt construction helpers that defend against:
  1. Prompt injection: user content trying to override system instructions.
  2. Excessive input length: prevents context overflow / cost inflation.
  3. Null-byte / control character smuggling.

Usage:
    from app.core.prompt_security import sanitize_user_content, wrap_user_content

    safe_text = sanitize_user_content(untrusted_string)
    prompt = (
        "System instructions here\\n\\n"
        + wrap_user_content(safe_text)
    )
"""

from __future__ import annotations

import re
import unicodedata

# ─── Constants ─────────────────────────────────────────────────────────────────

# Maximum characters of user content we will embed into any prompt.
# At ~4 chars/token this is ~10 000 tokens — generous but bounded.
MAX_USER_CONTENT_CHARS: int = 40_000

# Sentinel tags used to fence user-supplied content in prompts.
# LLMs are instructed to treat content between these tags as data, not commands.
_USER_CONTENT_OPEN = "[USER_CONTENT_START]"
_USER_CONTENT_CLOSE = "[USER_CONTENT_END]"

# Patterns that suggest an injection attempt.
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)ignore\s+(all\s+)?previous\s+instructions?"),
    re.compile(r"(?i)disregard\s+(all\s+)?previous"),
    re.compile(r"(?i)you\s+are\s+now\s+(a|an)\s+"),
    re.compile(r"(?i)(system|assistant)\s*:\s*"),  # fake role prefixes
    re.compile(r"(?i)<\s*/?\s*(system|user|assistant)\s*>"),  # XML role tags
    re.compile(r"IGNORE\s+SYSTEM"),
]


# ─── Public API ────────────────────────────────────────────────────────────────


def sanitize_user_content(text: str, max_chars: int = MAX_USER_CONTENT_CHARS) -> str:
    """
    Clean and truncate user-supplied text before embedding in an LLM prompt.

    Steps:
      1. Null-byte and non-printable control character removal.
      2. Unicode normalisation (NFC) to avoid homoglyph attacks.
      3. Truncation to `max_chars`.
      4. Soft injection-pattern detection with neutralisation (pattern → [REDACTED]).

    Args:
        text: Raw user-supplied string.
        max_chars: Hard cap on character count.

    Returns:
        Cleaned string safe for embedding in prompts.
    """
    if not isinstance(text, str):
        text = str(text)

    # Step 1: Remove null bytes and ASCII control characters (except tab/newline/CR)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Step 2: Normalise Unicode (NFC) — collapses composed forms
    text = unicodedata.normalize("NFC", text)

    # Step 3: Truncate
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[... content truncated for safety ...]"

    # Step 4: Neutralise injection patterns
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[REDACTED]", text)

    return text


def wrap_user_content(text: str) -> str:
    """
    Wrap already-sanitised user content in sentinel tags so the LLM can
    clearly distinguish it from system instructions.

    Example output:
        [USER_CONTENT_START]
        ...sanitised text...
        [USER_CONTENT_END]
    """
    return f"{_USER_CONTENT_OPEN}\n{text}\n{_USER_CONTENT_CLOSE}"


def safe_user_block(raw_text: str, max_chars: int = MAX_USER_CONTENT_CHARS) -> str:
    """
    Convenience combinator: sanitize + wrap in one call.

    Returns the fenced, cleaned user content block ready to append to a prompt.
    """
    return wrap_user_content(sanitize_user_content(raw_text, max_chars))
