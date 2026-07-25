"""
Pagination query parameter parsing using offset/limit.
"""

from fastapi import Query
from pydantic import BaseModel

from app.core.constants import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT


class OffsetParams(BaseModel):
    """Common pagination parameters using offset and limit."""

    offset: int = 0
    limit: int = DEFAULT_PAGE_LIMIT


def get_offset_params(
    offset: int = Query(default=0, ge=0, description="Offset number of items to skip"),
    limit: int = Query(
        default=DEFAULT_PAGE_LIMIT,
        ge=1,
        le=MAX_PAGE_LIMIT,
        description=f"Items per page (max {MAX_PAGE_LIMIT})",
    ),
) -> OffsetParams:
    """FastAPI dependency for pagination parameters."""
    return OffsetParams(offset=offset, limit=limit)
