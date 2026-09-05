"""Value classification — NO-FABRICATION policy (ADR-0009).

Every domain, engineering, financial, sensor, or AI value handled by PAEOS must
carry an explicit provenance classification. This module provides the canonical
enumeration and a lightweight wrapper for a classified value.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Generic, TypeVar


class Classification(StrEnum):
    """Provenance/quality classification for any reported value."""

    UNKNOWN = "UNKNOWN"
    ASSUMPTION = "ASSUMPTION"
    ESTIMATE = "ESTIMATE"
    SIMULATION = "SIMULATION"
    MEASURED = "MEASURED"
    VALIDATED = "VALIDATED"

    @property
    def is_trustworthy_for_decisions(self) -> bool:
        """Only measured/validated values may back safety/financial decisions."""
        return self in (Classification.MEASURED, Classification.VALIDATED)


T = TypeVar("T")


@dataclass(frozen=True)
class ClassifiedValue(Generic[T]):
    """A value paired with its provenance classification.

    Prevents raw, unlabeled numbers from silently entering the system. The
    foundation ships the mechanism; domain phases supply the values.
    """

    value: T
    classification: Classification
    unit: str | None = None
    source: str | None = None
    note: str | None = None

    def require(self, *allowed: Classification) -> ClassifiedValue[T]:
        """Raise if this value's classification is not in ``allowed``."""
        if self.classification not in allowed:
            allowed_names = ", ".join(c.value for c in allowed)
            raise ValueError(
                f"Value classification {self.classification.value} is not "
                f"permitted here (allowed: {allowed_names})."
            )
        return self
