from decimal import Decimal

import pytest

from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.logistics.models import SHIPMENT_WORKFLOW
from paeos_fx.trading.models import SALES_ORDER_WORKFLOW
from paeos_fx.trading.service import _line_total_minor

pytestmark = pytest.mark.unit


def test_sales_order_lifecycle():
    m = SALES_ORDER_WORKFLOW
    assert m.fire("draft", "confirm") == "confirmed"
    assert m.fire("confirmed", "fulfill") == "fulfilled"
    assert m.fire("fulfilled", "close") == "closed"


def test_cannot_fulfill_draft():
    with pytest.raises(BusinessRuleError):
        SALES_ORDER_WORKFLOW.fire("draft", "fulfill")


def test_shipment_lifecycle():
    m = SHIPMENT_WORKFLOW
    assert m.fire("planned", "dispatch") == "dispatched"
    assert m.fire("dispatched", "deliver") == "delivered"


def test_line_total_exact():
    assert _line_total_minor(1250, Decimal("3")) == 3750
    assert _line_total_minor(100, Decimal("2.5")) == 250
