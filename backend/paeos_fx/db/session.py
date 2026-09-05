"""Database engine + session management with tenant (RLS) binding (section D).

The session factory is configured once. :func:`tenant_session` opens a session
and sets the ``app.tenant_id`` PostgreSQL session variable inside a transaction,
which the Row-Level Security policies (defined in migrations) read to restrict
visible rows. No tenant-owned query should run without this binding.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from paeos_fx.core.config import Settings, get_settings

_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def get_engine(settings: Settings | None = None) -> Engine:
    global _engine
    if _engine is None:
        settings = settings or get_settings()
        _engine = create_engine(
            settings.database_url,
            echo=settings.db_echo,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
            future=True,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(
            bind=get_engine(), autoflush=False, expire_on_commit=False, future=True
        )
    return _SessionFactory


def _apply_tenant(session: Session, tenant_id: uuid.UUID | None) -> None:
    """Bind the RLS tenant variable for this session's transaction.

    Uses ``set_config(..., is_local => true)`` so the setting is scoped to the
    current transaction and cannot leak across pooled connections.
    """
    value = str(tenant_id) if tenant_id is not None else ""
    session.execute(
        text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": value}
    )


@contextmanager
def tenant_session(tenant_id: uuid.UUID | None) -> Iterator[Session]:
    """Yield a session with the tenant RLS variable applied for its lifetime."""
    factory = get_session_factory()
    session = factory()
    try:
        _apply_tenant(session, tenant_id)
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
