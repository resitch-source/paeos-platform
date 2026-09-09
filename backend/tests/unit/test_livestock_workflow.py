import pytest

from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.livestock.models import ANIMAL_GROUP_WORKFLOW

pytestmark = pytest.mark.unit


def test_animal_group_lifecycle():
    m = ANIMAL_GROUP_WORKFLOW
    assert m.initial == "established"
    assert m.fire("established", "activate") == "active"
    assert m.fire("active", "close") == "closed"


def test_illegal_transition_raises():
    with pytest.raises(BusinessRuleError):
        ANIMAL_GROUP_WORKFLOW.fire("established", "close")


def test_closed_is_terminal():
    assert not ANIMAL_GROUP_WORKFLOW.can_fire("closed", "activate")
