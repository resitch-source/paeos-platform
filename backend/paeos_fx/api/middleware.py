"""Request context + security middleware (sections U/W/AB)."""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from paeos_fx.core.context import ExecutionContext, reset_context, set_context
from paeos_fx.core.ratelimit import FixedWindowRateLimiter

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


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Additive, opt-in fixed-window rate limiter (defense in depth).

    Disabled unless ``rate_limit_enabled`` is set, so it changes no existing
    behavior or security boundary. Keying is by client host — a coarse throttle,
    not an authentication or tenant-isolation control.
    """

    def __init__(self, app, limit: int, window_seconds: int = 60):
        super().__init__(app)
        self._limiter = FixedWindowRateLimiter(limit=limit,
                                               window_seconds=window_seconds)

    async def dispatch(self, request: Request, call_next) -> Response:
        client = request.client.host if request.client else "unknown"
        if not self._limiter.allow(client, time.time()):
            return JSONResponse(
                status_code=429,
                content={"error": {"code": "rate_limited",
                                   "message": "Too many requests."}},
            )
        return await call_next(request)
