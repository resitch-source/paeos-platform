from decimal import Decimal

import pytest

from paeos_fx.ai.agents import low_stock_advisory, open_order_advisory
from paeos_fx.ai.models import RECOMMENDATION_WORKFLOW
from paeos_fx.ai.service import AGENTS
from paeos_fx.core.classification import Classification
from paeos_fx.core.context import ExecutionContext
from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.interfaces.ai import ToolResult
from paeos_fx.platform import permissions as perms

pytestmark = pytest.mark.unit


def _stock(*rows):
    return ToolResult(output=list(rows), classification=Classification.MEASURED,
                      confidence=1.0)


def test_low_stock_flags_only_below_threshold():
    result = _stock(
        {"item_id": "i1", "warehouse_id": "w1", "quantity": "5"},
        {"item_id": "i2", "warehouse_id": "w1", "quantity": "50"},
    )
    recs = low_stock_advisory(result, threshold=Decimal("10"))
    assert len(recs) == 1
    rec = recs[0]
    assert rec.classification == Classification.ESTIMATE
    assert rec.requires_human_approval is True
    assert rec.assumptions  # provenance recorded, not fabricated


def test_low_stock_empty_when_all_above():
    result = _stock({"item_id": "i", "warehouse_id": "w", "quantity": "100"})
    assert low_stock_advisory(result, threshold=Decimal("10")) == []


def test_open_order_advisory_flags_each():
    result = ToolResult(
        output=[{"id": "o1", "code": "SO1", "status": "confirmed"}],
        classification=Classification.MEASURED, confidence=1.0,
    )
    recs = open_order_advisory(result)
    assert len(recs) == 1
    assert recs[0].requires_human_approval is True


def test_recommendation_lifecycle():
    m = RECOMMENDATION_WORKFLOW
    assert m.fire("proposed", "accept") == "accepted"
    assert m.fire("proposed", "reject") == "rejected"
    assert m.fire("accepted", "supersede") == "superseded"


def test_cannot_accept_rejected():
    with pytest.raises(BusinessRuleError):
        RECOMMENDATION_WORKFLOW.fire("rejected", "accept")


def test_registered_agents_use_only_readonly_tools():
    """SAFETY: the Phase-10 registry must expose no mutating/safety-critical tool."""
    from paeos_fx.ai.tools import build_registry

    ctx = ExecutionContext(tenant_id=__import__("uuid").uuid4(),
                           permissions=frozenset(perms.TENANT_ADMIN_PERMISSIONS))
    registry = build_registry(session=None, ctx=ctx)  # handlers not invoked here
    for tool in registry._tools.values():  # noqa: SLF001 - white-box safety assertion
        assert tool.mutates is False
        assert tool.safety_critical is False
    # Every agent references a tool that exists in the registry.
    for spec in AGENTS.values():
        assert spec.tool_name in registry._tools  # noqa: SLF001
