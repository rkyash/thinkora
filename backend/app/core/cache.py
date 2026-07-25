"""
Redis client singleton and caching utilities.
"""

import functools
import hashlib
import json
from collections.abc import Callable
from typing import Any

import redis.asyncio as aioredis

from app.config import settings
from app.core.logging import logger

# Singleton Redis client
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection on shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def redis_ping() -> bool:
    """Health check: ping Redis."""
    try:
        client = await get_redis()
        return await client.ping()
    except Exception as e:
        logger.error("redis_ping_failed", error=str(e))
        return False


def _make_cache_key(prefix: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """Generate a deterministic cache key from function arguments."""
    key_data = json.dumps({"args": str(args), "kwargs": str(kwargs)}, sort_keys=True)
    key_hash = hashlib.md5(key_data.encode()).hexdigest()  # noqa: S324
    return f"cache:{prefix}:{key_hash}"


def cached(prefix: str, ttl_seconds: int = 300) -> Callable[..., Any]:
    """
    Decorator to cache async function results in Redis.

    Usage:
        @cached("embeddings", ttl_seconds=3600)
        async def get_embedding(text: str) -> list[float]:
            ...
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            client = await get_redis()
            cache_key = _make_cache_key(prefix, args, kwargs)

            # Try cache hit
            try:
                cached_value = await client.get(cache_key)
                if cached_value is not None:
                    return json.loads(cached_value)
            except Exception:
                logger.warning("cache_read_failed", key=cache_key)

            # Cache miss — execute function
            result = await func(*args, **kwargs)

            # Store in cache
            try:
                await client.setex(cache_key, ttl_seconds, json.dumps(result))
            except Exception:
                logger.warning("cache_write_failed", key=cache_key)

            return result

        return wrapper

    return decorator
