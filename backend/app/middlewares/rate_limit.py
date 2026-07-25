"""
Rate limiting middleware using slowapi with Redis backend.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter instance — uses client IP as key
# Import this in routers to apply per-endpoint limits:
#   @router.get("/", dependencies=[Depends(RateLimitDepends)])
#   @limiter.limit("10/minute")
#   async def my_endpoint(request: Request): ...
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=None,  # Will be set to Redis URI in main.py startup
)
