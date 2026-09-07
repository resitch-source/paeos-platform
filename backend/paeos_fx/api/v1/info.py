"""Build-info / release endpoint (Phase 13).

Public, read-only operational metadata: version, environment, build SHA, and the
completed-phase manifest. Exposes no tenant data or secrets.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from paeos_fx.platform.release import (
    CAPABILITY_BUNDLES,
    PHASE_MANIFEST,
    RELEASE_VERSION,
    build_sha,
)

router = APIRouter(tags=["info"])


@router.get("/info")
async def info(request: Request) -> dict:
    """Describe the released build (version, phases, capabilities)."""
    settings = getattr(request.app.state, "settings", None)
    environment = getattr(settings, "environment", "unknown")
    return {
        "product": "PAEOS",
        "description": "Philippine Agriculture Enterprise Operating System",
        "version": RELEASE_VERSION,
        "environment": environment,
        "build_sha": build_sha(),
        "phases": [dict(p) for p in PHASE_MANIFEST],
        "capability_bundles": {k: list(v) for k, v in CAPABILITY_BUNDLES.items()},
    }
