from decimal import Decimal

import pytest

from paeos_fx.core.errors import ValidationError
from paeos_fx.platform.uom import default_registry

pytestmark = pytest.mark.unit


def test_mass_conversion():
    reg = default_registry()
    assert reg.convert(1, "kg", "g") == Decimal("1000")
    assert reg.convert(2500, "g", "kg") == Decimal("2.5")
    assert reg.convert(1, "t", "kg") == Decimal("1000")


def test_area_conversion_hectare():
    reg = default_registry()
    assert reg.convert(1, "ha", "m2") == Decimal("10000")


def test_cross_dimension_rejected():
    reg = default_registry()
    with pytest.raises(ValidationError):
        reg.convert(1, "kg", "m")


def test_unknown_unit_rejected():
    reg = default_registry()
    with pytest.raises(ValidationError):
        reg.convert(1, "kg", "furlong")
