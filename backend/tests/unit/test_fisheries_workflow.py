import pytest

from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.fisheries.models import AQUACULTURE_CYCLE_WORKFLOW

pytestmark = pytest.mark.unit


def test_aquaculture_lifecycle():
    m = AQUACULTURE_CYCLE_WORKFLOW
    assert m.initial == "stocked"
    assert m.fire("stocked", "start_growth") == "growing"
    assert m.fire("growing", "harvest") == "harvested"
    assert m.fire("harvested", "close") == "closed"


def test_illegal_transition_raises():
    with pytest.raises(BusinessRuleError):
        AQUACULTURE_CYCLE_WORKFLOW.fire("stocked", "harvest")
