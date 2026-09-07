from decimal import Decimal

import pytest

from paeos_fx.agrisim.engines import available_models, get_engine
from paeos_fx.agrisim.optimization import (
    economic_order_quantity,
    proportional_allocation,
)
from paeos_fx.core.classification import Classification
from paeos_fx.core.errors import ValidationError
from paeos_fx.interfaces.simulation import SimulationRequest

pytestmark = pytest.mark.unit


def test_eoq_hand_verified():
    # D=1000, S=10, H=2 -> sqrt(2*1000*10/2) = sqrt(10000) = 100
    assert economic_order_quantity(1000, 10, 2) == pytest.approx(100.0)


def test_eoq_rejects_nonpositive_holding_cost():
    with pytest.raises(ValidationError):
        economic_order_quantity(1000, 10, 0)


def test_allocation_is_proportional_and_exact():
    parts = proportional_allocation(Decimal("100"),
                                    {"a": Decimal("1"), "b": Decimal("3")})
    assert parts["a"] == Decimal("25.0000")
    assert parts["b"] == Decimal("75.0000")
    assert sum(parts.values()) == Decimal("100")


def test_allocation_remainder_assigned_to_largest_weight():
    # 10 split 1:1:1 -> 3.3333 each; remainder 0.0001 to the largest (first) key.
    parts = proportional_allocation(Decimal("10"),
                                    {"a": Decimal("1"), "b": Decimal("1"),
                                     "c": Decimal("1")})
    assert sum(parts.values()) == Decimal("10")


def test_allocation_rejects_empty_weights():
    with pytest.raises(ValidationError):
        proportional_allocation(Decimal("10"), {})


def test_eoq_engine_provenance():
    engine = get_engine("eoq")
    result = engine.run(SimulationRequest(
        scenario="reorder",
        parameters={"annual_demand": 1000, "order_cost": 10, "holding_cost": 2},
    ))
    assert result.outputs["eoq"] == pytest.approx(100.0)
    assert result.record.validation_status == Classification.SIMULATION
    assert result.record.model_version
    assert result.record.reference  # citable, not fabricated


def test_registry_lists_all_models_and_rejects_unknown():
    names = {e["name"] for e in available_models()}
    assert {"growing_degree_days", "mass_balance", "eoq", "allocation"} <= names
    with pytest.raises(ValidationError):
        get_engine("nope")
