"""Integration fixtures: build the platform schema on a live PostgreSQL.

Two fixtures are provided:

- ``enterprise_db`` / ``session_factory`` — create only the NON-geometry tables
  (all IAM/tenancy/org and agriculture master-data tables). Runs on any
  PostgreSQL, no PostGIS required.
- ``gis_db`` / ``gis_session_factory`` — create ALL tables including PostGIS
  geometry tables. Skipped unless PostGIS is installed on the target database.

Both apply Row-Level Security to the tenant-owned tables they create.
"""

from __future__ import annotations

import pytest
from geoalchemy2 import Geometry
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

import paeos_fx.db.registry as registry  # noqa: F401 - registers all models
from paeos_fx.db.base import PLATFORM_SCHEMA, metadata


def _has_geometry(table) -> bool:
    return any(isinstance(c.type, Geometry) for c in table.columns)


def _non_geometry_tables() -> list:
    return [t for t in metadata.sorted_tables if not _has_geometry(t)]


def _apply_rls(conn, table_names: set[str]) -> None:
    for table in registry.TENANT_OWNED_TABLES:
        if table not in table_names:
            continue
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


def _postgis_available(engine) -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT postgis_version()"))
        return True
    except Exception:
        return False


@pytest.fixture()
def enterprise_db(engine):
    """Create non-geometry tables + RLS; drop them on teardown."""
    tables = _non_geometry_tables()
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {PLATFORM_SCHEMA}"))
    metadata.create_all(engine, tables=tables)
    names = {t.name for t in tables}
    with engine.begin() as conn:
        _apply_rls(conn, names)
    yield engine
    metadata.drop_all(engine, tables=tables)
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {PLATFORM_SCHEMA} CASCADE"))


@pytest.fixture()
def session_factory(enterprise_db) -> sessionmaker[Session]:
    return sessionmaker(bind=enterprise_db, expire_on_commit=False, future=True)


@pytest.fixture()
def gis_db(engine):
    """Create ALL tables (incl. PostGIS geometry) + RLS. Requires PostGIS."""
    if not _postgis_available(engine):
        pytest.skip("PostGIS not available on the target database.")
    with engine.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {PLATFORM_SCHEMA}"))
    metadata.create_all(engine)
    names = {t.name for t in metadata.sorted_tables}
    with engine.begin() as conn:
        _apply_rls(conn, names)
    yield engine
    metadata.drop_all(engine)
    with engine.begin() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {PLATFORM_SCHEMA} CASCADE"))


@pytest.fixture()
def gis_session_factory(gis_db) -> sessionmaker[Session]:
    return sessionmaker(bind=gis_db, expire_on_commit=False, future=True)
