import pytest

from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.platform.workflow import StateMachine, Transition

pytestmark = pytest.mark.unit


def make_machine() -> StateMachine:
    return StateMachine(
        states=frozenset({"draft", "submitted", "approved", "rejected"}),
        initial="draft",
        transitions=[
            Transition("draft", "submitted", "submit"),
            Transition("submitted", "approved", "approve"),
            Transition("submitted", "rejected", "reject"),
        ],
    )


def test_valid_transition():
    m = make_machine()
    assert m.fire("draft", "submit") == "submitted"
    assert m.fire("submitted", "approve") == "approved"


def test_illegal_transition_raises():
    m = make_machine()
    with pytest.raises(BusinessRuleError):
        m.fire("draft", "approve")


def test_guarded_transition():
    m = StateMachine(
        states=frozenset({"open", "closed"}),
        initial="open",
        transitions=[
            Transition("open", "closed", "close", guard=lambda d: d.get("ok") is True)
        ],
    )
    assert m.can_fire("open", "close", {"ok": True})
    assert not m.can_fire("open", "close", {"ok": False})


def test_invalid_initial_state():
    with pytest.raises(ValueError):
        StateMachine(states=frozenset({"a"}), initial="b")
