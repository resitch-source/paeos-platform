from decimal import Decimal

import pytest

from paeos_fx.core.errors import ValidationError
from paeos_fx.platform.currency import (
    Money,
    UnconfiguredExchangeRateProvider,
)

pytestmark = pytest.mark.unit


def test_money_from_decimal_php():
    m = Money.from_decimal("123.45", "PHP")
    assert m.amount_minor == 12345
    assert m.currency == "PHP"
    assert m.to_decimal() == Decimal("123.45")


def test_money_zero_decimal_currency():
    m = Money.from_decimal("1000", "JPY")
    assert m.amount_minor == 1000  # JPY has 0 minor units


def test_money_add_same_currency():
    total = Money(1000, "PHP").add(Money(500, "PHP"))
    assert total.amount_minor == 1500


def test_money_currency_mismatch_rejected():
    with pytest.raises(ValidationError):
        Money(1000, "PHP").add(Money(500, "USD"))


def test_unconfigured_fx_refuses_to_fabricate():
    provider = UnconfiguredExchangeRateProvider()
    with pytest.raises(ValidationError):
        provider.rate("USD", "PHP")
