"""API v1 aggregate router.

Only foundation endpoints (health/readiness, and a meta endpoint describing the
platform) are mounted. Domain routers are added by their respective phases.
"""

from __future__ import annotations

from fastapi import APIRouter

from paeos_fx import __version__
from paeos_fx.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)


@api_router.get("/meta", tags=["meta"])
async def meta() -> dict:
    """Describe the foundation build and its active phase."""
    return {
        "product": "PAEOS",
        "component": "PAEOS-FX Foundation",
        "version": __version__,
        "active_phase": "FOUNDATION",
        "domain_phases_started": [],
    }
