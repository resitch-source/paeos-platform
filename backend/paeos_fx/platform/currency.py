"""Currency engine (section R).

A precise :class:`Money` value type stored as integer minor units (avoids float
rounding error), plus an FX-rate provider *interface*. No exchange rates are
hardcoded — rates are supplied by an external provider and always carry a
provenance classification (never fabricated). Financial *transaction logic* is
out of scope for the foundation and is a gated concern.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Protocol

from paeos_fx.core.classification import ClassifiedValue
from paeos_fx.core.errors import ValidationError

# Minor-unit exponents for currencies used at the foundation.
_MINOR_UNITS: dict[str, int] = {"PHP": 2, "USD": 2, "EUR": 2, "JPY": 0}


def minor_units(currency: str) -> int:
    return _MINOR_UNITS.get(currency.upper(), 2)


@dataclass(frozen=True)
class Money:
    """An exact monetary amount in integer minor units (e.g. centavos)."""

    amount_minor: int
    currency: str

    @classmethod
    def from_decimal(cls, amount: Decimal | str | int, currency: str) -> Money:
        exp = minor_units(currency)
        quant = Decimal(1).scaleb(-exp)
        value = (Decimal(str(amount)) / quant).to_integral_value(
            rounding=ROUND_HALF_UP
        )
        return cls(int(value), currency.upper())

    def to_decimal(self) -> Decimal:
        return Decimal(self.amount_minor).scaleb(-minor_units(self.currency))

    def _check(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValidationError(
                f"Currency mismatch: {self.currency} vs {other.currency}"
            )

    def add(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount_minor + other.amount_minor, self.currency)

    def subtract(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount_minor - other.amount_minor, self.currency)

    def __str__(self) -> str:
        return f"{self.to_decimal()} {self.currency}"


class ExchangeRateProvider(Protocol):
    """Minimum stable interface for FX rates.

    Implementations must return a classified rate; the foundation ships no rate
    source, so unconfigured conversions fail rather than fabricate a rate.
    """

    def rate(self, base: str, quote: str) -> ClassifiedValue[Decimal]: ...


class UnconfiguredExchangeRateProvider:
    """Default provider that refuses to invent rates (NO-FABRICATION)."""

    def rate(self, base: str, quote: str) -> ClassifiedValue[Decimal]:
        raise ValidationError(
            "No exchange-rate provider configured; refusing to fabricate a rate "
            f"for {base}->{quote}."
        )
