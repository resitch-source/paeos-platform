from decimal import Decimal

import pytest

from paeos_fx.platform.currency import Money
from paeos_fx.procurement.service import _line_total_minor

pytestmark = pytest.mark.unit


def test_line_total_exact():
    # 12.50 PHP * 3 = 37.50 -> 3750 minor units.
    price = Money.from_decimal("12.50", "PHP")
    assert price.amount_minor == 1250
    assert _line_total_minor(price.amount_minor, Decimal("3")) == 3750


def test_line_total_fractional_quantity_rounds_half_up():
    # 100 centavos * 2.5 = 250 -> 250 minor units.
    assert _line_total_minor(100, Decimal("2.5")) == 250
    # 3 * 0.3333 = 0.9999 -> rounds to 1 minor unit.
    assert _line_total_minor(3, Decimal("0.3333")) == 1


def test_money_roundtrip():
    m = Money.from_decimal("1999.99", "PHP")
    assert m.amount_minor == 199999
    assert m.to_decimal() == Decimal("1999.99")
