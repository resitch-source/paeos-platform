"""Declarative base with consistent naming conventions (section C).

Deterministic constraint/index names keep Alembic migrations stable and make
schema diffs reviewable.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# The platform framework lives in its own schema to keep foundation objects
# clearly separated from future domain schemas.
PLATFORM_SCHEMA = "platform"

metadata = MetaData(
    naming_convention=NAMING_CONVENTION,
    schema=PLATFORM_SCHEMA,
)


class Base(DeclarativeBase):
    """Root declarative base for all PAEOS ORM models."""

    metadata = metadata
