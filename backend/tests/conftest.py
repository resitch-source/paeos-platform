"""Shared pytest fixtures.

Integration tests require a live PostgreSQL+PostGIS database. Point
``PAEOS_TEST_DATABASE_URL`` at one to enable them; otherwise they are skipped so
the unit suite always runs green in any environment.
"""

from __future__ import annotations

import os

import pytest

TEST_DB_URL = os.environ.get("PAEOS_TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def db_url() -> str:
    if not TEST_DB_URL:
        pytest.skip("PAEOS_TEST_DATABASE_URL not set; skipping DB integration tests.")
    return TEST_DB_URL


@pytest.fixture(scope="session")
def engine(db_url):
    from sqlalchemy import create_engine

    eng = create_engine(db_url, future=True)
    yield eng
    eng.dispose()
