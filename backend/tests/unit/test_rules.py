import pytest

from paeos_fx.platform.rules import Condition, Rule, RuleSet

pytestmark = pytest.mark.unit


def test_rule_matches_all_conditions():
    rule = Rule(
        name="high_moisture",
        conditions=[
            Condition("moisture_pct", "gt", 14),
            Condition("crop", "eq", "rice"),
        ],
        actions={"flag": "reject"},
    )
    assert rule.matches({"moisture_pct": 16, "crop": "rice"})
    assert not rule.matches({"moisture_pct": 10, "crop": "rice"})
    assert not rule.matches({"moisture_pct": 16, "crop": "corn"})


def test_ruleset_collect_actions_merges():
    rs = RuleSet(
        [
            Rule("a", [Condition("x", "gte", 1)], {"k1": 1}),
            Rule("b", [Condition("x", "gte", 2)], {"k2": 2}),
        ]
    )
    assert rs.collect_actions({"x": 5}) == {"k1": 1, "k2": 2}
    assert rs.collect_actions({"x": 1}) == {"k1": 1}


def test_unknown_operator_raises():
    with pytest.raises(ValueError):
        Condition("x", "bogus", 1).evaluate({"x": 1})
