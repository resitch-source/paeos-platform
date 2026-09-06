import pytest

from paeos_fx.core.errors import BusinessRuleError
from paeos_fx.experts.models import ENGAGEMENT_WORKFLOW
from paeos_fx.support.models import SUPPORT_TICKET_WORKFLOW
from paeos_fx.training.models import ENROLLMENT_WORKFLOW

pytestmark = pytest.mark.unit


def test_enrollment_lifecycle():
    m = ENROLLMENT_WORKFLOW
    assert m.fire("enrolled", "start") == "in_progress"
    assert m.fire("in_progress", "complete") == "completed"
    assert m.fire("enrolled", "withdraw") == "withdrawn"
    assert m.fire("in_progress", "withdraw") == "withdrawn"


def test_cannot_complete_before_start():
    with pytest.raises(BusinessRuleError):
        ENROLLMENT_WORKFLOW.fire("enrolled", "complete")


def test_support_ticket_lifecycle():
    m = SUPPORT_TICKET_WORKFLOW
    assert m.fire("open", "assign") == "in_progress"
    assert m.fire("in_progress", "resolve") == "resolved"
    assert m.fire("resolved", "close") == "closed"
    assert m.fire("resolved", "reopen") == "in_progress"


def test_cannot_close_open_ticket():
    with pytest.raises(BusinessRuleError):
        SUPPORT_TICKET_WORKFLOW.fire("open", "close")


def test_engagement_lifecycle():
    m = ENGAGEMENT_WORKFLOW
    assert m.fire("requested", "accept") == "accepted"
    assert m.fire("accepted", "deliver") == "delivered"
    assert m.fire("delivered", "close") == "closed"
    assert m.fire("requested", "cancel") == "cancelled"


def test_cannot_deliver_unaccepted_engagement():
    with pytest.raises(BusinessRuleError):
        ENGAGEMENT_WORKFLOW.fire("requested", "deliver")
