"""Health & readiness endpoints (sections U/W)."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from paeos_fx import __version__
from paeos_fx.db.session import get_engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness probe: process is up. Does not touch dependencies."""
    return {"status": "ok", "version": __version__}


@router.get("/ready")
async def ready() -> dict:
    """Readiness probe: verifies the database is reachable."""
    db_ok = True
    detail = "ok"
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - depends on live DB
        db_ok = False
        detail = f"database unavailable: {type(exc).__name__}"
    return {
        "status": "ok" if db_ok else "degraded",
        "checks": {"database": {"ok": db_ok, "detail": detail}},
    }
