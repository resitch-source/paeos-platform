import pytest

from paeos_fx.platform.numbering import NumberSequence, format_number

pytestmark = pytest.mark.unit


def test_format_with_prefix_and_year():
    seq = NumberSequence(prefix="INV", padding=6)
    assert format_number(seq, 42, year=2026) == "INV-2026-000042"


def test_format_without_year():
    seq = NumberSequence(prefix="PO", padding=4)
    assert format_number(seq, 7) == "PO-0007"


def test_format_no_prefix():
    seq = NumberSequence(prefix="", padding=3)
    assert format_number(seq, 5) == "005"
