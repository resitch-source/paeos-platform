"""Integration fixtures: build the platform schema on a live PostgreSQL.

Uses ``Base.metadata.create_all`` (no PostGIS required) plus Row-Level Security
policies, so these tests run against any PostgreSQL pointed at by
``PAEOS_TEST_DATABASE_URL`` — including the CI PostGIS service.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

import paeos_fx.db.registry as registry  # noqa: F401 - registers all models
from paeos_fx.db.base import PLATFORM_SCHEMA, metadata


@pytest.fixture()
def enterprise_db(engine):
    """Create the platform schema + tables + RLS; drop it on teardown."""
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {PLATFORM_SCHEMA}"))
    metadata.create_all(engine)
    with engine.begin() as conn:
        for table in registry.TENANT_OWNED_TABLES:
            fq = f"{PLATFORM_SCHEMA}.{table}"
            conn.execute(text(f"ALTER TABLE {fq} ENABLE ROW LEVEL SECURITY"))
            conn.execute(text(f"ALTER TABLE {fq} FORCE ROW LEVEL SECURITY"))
            conn.execute(
                text(
                    f"CREATE POLICY tenant_isolation ON {fq} "
                    "USING (tenant_id::text = current_setting('app.tenant_id', true)) "
                    "WITH CHECK (tenant_id::text = current_setting('app.tenant_id', true))"
                )
            )
    yield engine
    metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {PLATFORM_SCHEMA} CASCADE"))


@pytest.fixture()
def session_factory(enterprise_db) -> sessionmaker[Session]:
    return sessionmaker(bind=enterprise_db, expire_on_commit=False, future=True)
