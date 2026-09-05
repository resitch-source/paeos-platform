"""Map PAEOS exceptions to consistent HTTP error envelopes (section V)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from paeos_fx.core.context import current_context
from paeos_fx.core.errors import PaeosError
from paeos_fx.core.logging import get_logger

logger = get_logger("paeos.api.errors")


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(PaeosError)
    async def _handle_paeos_error(request: Request, exc: PaeosError):
        correlation_id = current_context().correlation_id
        logger.warning(
            "handled_error", code=exc.code, path=request.url.path, message=exc.message
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_envelope(correlation_id),
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception):
        correlation_id = current_context().correlation_id
        # Never leak internal details to the client.
        logger.error("unhandled_error", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "details": {},
                    "correlation_id": correlation_id,
                }
            },
        )
