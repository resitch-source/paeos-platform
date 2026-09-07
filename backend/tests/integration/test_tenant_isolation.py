"""Tenant-isolation negative tests (mandatory, section D / MULTI-TENANCY).

Proves at the database level that Tenant A cannot read or write Tenant B's rows
under Row-Level Security. Requires a live PostgreSQL+PostGIS database via
``PAEOS_TEST_DATABASE_URL``; skipped otherwise.

RLS is bypassed by superusers, so these tests run their assertions through a
dedicated NON-superuser role. Setup (which must see all rows) runs as the admin
connection.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = [pytest.mark.integration, pytest.mark.tenant_isolation]

APP_ROLE = "paeos_rls_test_app"
APP_ROLE_PW = "rls_test_pw"


@pytest.fixture()
def migrated_db(engine):
    """Apply the baseline migration and provision a non-superuser app role.

    Requires PostGIS (the baseline migration enables it); skipped otherwise.
    """
    from alembic import command
    from alembic.config import Config

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT postgis_version()"))
    except Exception:
        pytest.skip("PostGIS not available on the target database.")

    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    # Escape '%' so configparser interpolation does not choke on URL-encoded
    # socket hosts (e.g. host=%2Ftmp/...).
    cfg.set_main_option("sqlalchemy.url", str(engine.url).replace("%", "%%"))
    # Start from a clean slate so a schema left by a sibling fixture (the
    # create_all-based fixtures) does not collide with the migration run.
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS platform CASCADE"))
    command.upgrade(cfg, "head")

    with engine.begin() as conn:
        conn.execute(text(f"DROP ROLE IF EXISTS {APP_ROLE}"))
        conn.execute(
            text(f"CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_ROLE_PW}'")
        )
        conn.execute(text(f"GRANT USAGE ON SCHEMA platform TO {APP_ROLE}"))
        conn.execute(
            text(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA "
                f"platform TO {APP_ROLE}"
            )
        )
    yield engine
    with engine.begin() as conn:
        conn.execute(
            text(
                "REVOKE ALL ON ALL TABLES IN SCHEMA platform FROM " + APP_ROLE
            )
        )
        conn.execute(text(f"REVOKE USAGE ON SCHEMA platform FROM {APP_ROLE}"))
        conn.execute(text(f"DROP ROLE IF EXISTS {APP_ROLE}"))
        # Drop the migrated schema so sibling fixtures start clean (mirrors the
        # create_all-based fixtures, which drop the schema on teardown).
        conn.execute(text("DROP SCHEMA IF EXISTS platform CASCADE"))


def _app_engine(admin_engine):
    from sqlalchemy import create_engine

    url = admin_engine.url.set(username=APP_ROLE, password=APP_ROLE_PW)
    return create_engine(url, future=True)


def test_tenant_cannot_read_other_tenant(migrated_db):
    admin = migrated_db
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()

    # Seed one tenant + a setting row for each (admin bypasses RLS for setup).
    with admin.begin() as conn:
        for tid, slug in ((tenant_a, "tenant-a"), (tenant_b, "tenant-b")):
            conn.execute(
                text(
                    "INSERT INTO platform.tenant (id, slug, name) "
                    "VALUES (:id, :slug, :name)"
                ),
                {"id": tid, "slug": slug, "name": slug},
            )
            conn.execute(
                text(
                    "INSERT INTO platform.tenant_setting (id, tenant_id, key, value) "
                    "VALUES (:id, :tid, 'k', '{}'::jsonb)"
                ),
                {"id": uuid.uuid4(), "tid": tid},
            )

    app_engine = _app_engine(admin)
    try:
        # As tenant A, only tenant A's setting row is visible.
        with app_engine.connect() as conn:
            conn.execute(
                text("SELECT set_config('app.tenant_id', :tid, false)"),
                {"tid": str(tenant_a)},
            )
            rows = conn.execute(
                text("SELECT tenant_id FROM platform.tenant_setting")
            ).fetchall()
            assert len(rows) == 1
            assert rows[0][0] == tenant_a

        # As tenant B, only tenant B's row is visible.
        with app_engine.connect() as conn:
            conn.execute(
                text("SELECT set_config('app.tenant_id', :tid, false)"),
                {"tid": str(tenant_b)},
            )
            rows = conn.execute(
                text("SELECT tenant_id FROM platform.tenant_setting")
            ).fetchall()
            assert len(rows) == 1
            assert rows[0][0] == tenant_b
    finally:
        app_engine.dispose()


def test_tenant_cannot_insert_for_other_tenant(migrated_db):
    admin = migrated_db
    tenant_a = uuid.uuid4()
    tenant_b = uuid.uuid4()
    with admin.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO platform.tenant (id, slug, name) "
                "VALUES (:id, :slug, :name)"
            ),
            {"id": tenant_a, "slug": "tenant-a2", "name": "a"},
        )

    app_engine = _app_engine(admin)
    try:
        with app_engine.connect() as conn:
            conn.execute(
                text("SELECT set_config('app.tenant_id', :tid, false)"),
                {"tid": str(tenant_a)},
            )
            # Attempt to write a row belonging to tenant B -> WITH CHECK violation.
            with pytest.raises(DBAPIError):
                conn.execute(
                    text(
                        "INSERT INTO platform.tenant_setting "
                        "(id, tenant_id, key, value) "
                        "VALUES (:id, :tid, 'k', '{}'::jsonb)"
                    ),
                    {"id": uuid.uuid4(), "tid": tenant_b},
                )
                conn.commit()
    finally:
        app_engine.dispose()


def test_no_tenant_context_sees_nothing(migrated_db):
    admin = migrated_db
    tenant_a = uuid.uuid4()
    with admin.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO platform.tenant (id, slug, name) "
                "VALUES (:id, :slug, :name)"
            ),
            {"id": tenant_a, "slug": "tenant-a3", "name": "a"},
        )
        conn.execute(
            text(
                "INSERT INTO platform.tenant_setting (id, tenant_id, key, value) "
                "VALUES (:id, :tid, 'k', '{}'::jsonb)"
            ),
            {"id": uuid.uuid4(), "tid": tenant_a},
        )

    app_engine = _app_engine(admin)
    try:
        with app_engine.connect() as conn:
            # No app.tenant_id set -> fail-closed, zero rows.
            rows = conn.execute(
                text("SELECT * FROM platform.tenant_setting")
            ).fetchall()
            assert rows == []
    finally:
        app_engine.dispose()
