"""
Request ID middleware — injects X-Request-ID on every request/response
and binds it to structlog context for distributed tracing.
"""

from uuid import uuid4

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Inject X-Request-ID header and bind to structlog context."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Use client-provided ID or generate one
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        # Bind to structlog context (available in all async calls)
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        # Store on request state for access in dependencies
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response
