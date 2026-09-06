"""FastAPI application factory (section U).

Wires configuration, logging, middleware, error handling, and the v1 router.
Domain routers are intentionally absent — this is the foundation.
"""

from __future__ import annotations

from fastapi import FastAPI

from paeos_fx import __version__
from paeos_fx.api.errors import install_exception_handlers
from paeos_fx.api.middleware import ContextMiddleware
from paeos_fx.api.v1.router import api_router
from paeos_fx.core.config import Settings, get_settings
from paeos_fx.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    settings.assert_production_safe()
    configure_logging(level=settings.log_level, json_output=settings.log_json)

    app = FastAPI(
        title="PAEOS-FX Foundation API",
        version=__version__,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.state.settings = settings
    app.add_middleware(ContextMiddleware)
    install_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
