import pytest

from paeos_fx.core.classification import Classification, ClassifiedValue

pytestmark = pytest.mark.unit


def test_trustworthy_flag():
    assert Classification.MEASURED.is_trustworthy_for_decisions
    assert Classification.VALIDATED.is_trustworthy_for_decisions
    assert not Classification.ESTIMATE.is_trustworthy_for_decisions
    assert not Classification.ASSUMPTION.is_trustworthy_for_decisions


def test_require_allows_permitted_classification():
    cv = ClassifiedValue(42.0, Classification.MEASURED, unit="kg")
    assert cv.require(Classification.MEASURED, Classification.VALIDATED) is cv


def test_require_rejects_disallowed_classification():
    cv = ClassifiedValue(3.14, Classification.ASSUMPTION)
    with pytest.raises(ValueError):
        cv.require(Classification.MEASURED)
