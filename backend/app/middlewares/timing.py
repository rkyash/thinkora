"""
Timing middleware — adds X-Process-Time header and logs slow requests.
"""

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import logger

SLOW_REQUEST_THRESHOLD_MS = 2000


class TimingMiddleware(BaseHTTPMiddleware):
    """Measure request processing time and log slow requests."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

        if duration_ms > SLOW_REQUEST_THRESHOLD_MS:
            logger.warning(
                "slow_request",
                path=str(request.url.path),
                method=request.method,
                duration_ms=round(duration_ms, 2),
            )

        return response
