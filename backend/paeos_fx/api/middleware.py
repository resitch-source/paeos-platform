"""Request context + security middleware (sections U/W/AB)."""

from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from paeos_fx.core.context import ExecutionContext, reset_context, set_context

CORRELATION_HEADER = "X-Correlation-ID"

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


class ContextMiddleware(BaseHTTPMiddleware):
    """Establish a per-request execution context with a correlation id.

    Tenant/user binding is performed by the auth dependency once credentials are
    resolved; this middleware guarantees a context and correlation id exist for
    every request (including unauthenticated ones) so logs and errors correlate.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get(CORRELATION_HEADER) or str(uuid.uuid4())
        token = set_context(ExecutionContext(correlation_id=correlation_id))
        try:
            response = await call_next(request)
        finally:
            reset_context(token)
        response.headers[CORRELATION_HEADER] = correlation_id
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response
