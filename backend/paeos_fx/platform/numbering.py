"""Numbering engine (section P).

Gap-safe, per-tenant, per-document-type sequence numbers with configurable
formatting (prefix, zero-padded counter, optional year). Concurrency safety is
provided by a row lock on the sequence during increment (``SELECT ... FOR
UPDATE`` performed by the caller's session against PostgreSQL).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import BigInteger, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from paeos_fx.db.base import Base
from paeos_fx.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class NumberSequence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persistent counter for a (tenant, document type) pair."""

    __tablename__ = "number_sequence"
    __table_args__ = (UniqueConstraint("tenant_id", "doc_type"),)

    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), default="")
    padding: Mapped[int] = mapped_column(default=6, nullable=False)
    current_value: Mapped[int] = mapped_column(
        BigInteger, default=0, nullable=False
    )


@dataclass(frozen=True)
class FormattedNumber:
    value: int
    formatted: str


def format_number(seq: NumberSequence, value: int, *, year: int | None = None) -> str:
    """Render a sequence value, e.g. ``INV-2026-000042``."""
    parts = [p for p in (seq.prefix, str(year) if year else None) if p]
    parts.append(str(value).zfill(seq.padding))
    return "-".join(parts)


class NumberingService:
    """Allocate the next number for a document type (gap-safe)."""

    def __init__(self, session):
        self.session = session

    def next(self, seq: NumberSequence, *, year: int | None = None) -> FormattedNumber:
        seq.current_value += 1
        self.session.flush()
        return FormattedNumber(
            value=seq.current_value,
            formatted=format_number(seq, seq.current_value, year=year),
        )
