"""Units of measure engine (section Q).

Dimensional unit registry with safe conversions. Conversions are only allowed
within the same physical dimension; converting across dimensions (e.g. mass to
length) raises. Factors are expressed relative to a canonical base unit per
dimension.

All factors here are exact SI/definitional conversions (VALIDATED). No
agricultural or domain-specific coefficients are defined at the foundation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from paeos_fx.core.errors import ValidationError


@dataclass(frozen=True)
class Unit:
    code: str
    dimension: str
    # Multiply a value in this unit by ``to_base`` to get the base unit value.
    to_base: Decimal


# Canonical, definitional conversion factors (VALIDATED provenance).
_UNITS: dict[str, Unit] = {
    # Mass (base: kilogram)
    "kg": Unit("kg", "mass", Decimal("1")),
    "g": Unit("g", "mass", Decimal("0.001")),
    "mg": Unit("mg", "mass", Decimal("0.000001")),
    "t": Unit("t", "mass", Decimal("1000")),  # metric tonne
    # Length (base: metre)
    "m": Unit("m", "length", Decimal("1")),
    "cm": Unit("cm", "length", Decimal("0.01")),
    "mm": Unit("mm", "length", Decimal("0.001")),
    "km": Unit("km", "length", Decimal("1000")),
    # Area (base: square metre)
    "m2": Unit("m2", "area", Decimal("1")),
    "ha": Unit("ha", "area", Decimal("10000")),  # hectare
    # Volume (base: litre)
    "l": Unit("l", "volume", Decimal("1")),
    "ml": Unit("ml", "volume", Decimal("0.001")),
    "m3": Unit("m3", "volume", Decimal("1000")),
    # Count (base: each)
    "ea": Unit("ea", "count", Decimal("1")),
}


class UomRegistry:
    """Registry + conversion for units of measure."""

    def __init__(self, units: dict[str, Unit] | None = None) -> None:
        self._units = dict(units or _UNITS)

    def get(self, code: str) -> Unit:
        try:
            return self._units[code]
        except KeyError as exc:
            raise ValidationError(f"Unknown unit of measure: {code!r}") from exc

    def register(self, unit: Unit) -> None:
        self._units[unit.code] = unit

    def convert(self, value: Decimal | float | int, frm: str, to: str) -> Decimal:
        """Convert ``value`` from unit ``frm`` to unit ``to`` (same dimension)."""
        u_from = self.get(frm)
        u_to = self.get(to)
        if u_from.dimension != u_to.dimension:
            raise ValidationError(
                "Cannot convert across dimensions "
                f"({u_from.dimension} -> {u_to.dimension})."
            )
        base_value = Decimal(str(value)) * u_from.to_base
        return base_value / u_to.to_base


_default_registry = UomRegistry()


def default_registry() -> UomRegistry:
    return _default_registry
