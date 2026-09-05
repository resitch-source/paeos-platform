"""Rules engine (section J).

A small, safe declarative rule evaluator. Rules are data (not code): each rule
has a list of conditions over a fact dict and a set of resulting actions. No
arbitrary code execution — only whitelisted comparison operators — so rules can
safely originate from configuration or (later) AI proposals subject to approval.
"""

from __future__ import annotations

import operator
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": operator.eq,
    "ne": operator.ne,
    "lt": operator.lt,
    "lte": operator.le,
    "gt": operator.gt,
    "gte": operator.ge,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "contains": lambda a, b: b in a,
}


@dataclass(frozen=True)
class Condition:
    field: str
    op: str
    value: Any

    def evaluate(self, facts: dict[str, Any]) -> bool:
        if self.op not in _OPERATORS:
            raise ValueError(f"Unknown operator: {self.op}")
        return _OPERATORS[self.op](facts.get(self.field), self.value)


@dataclass(frozen=True)
class Rule:
    """All conditions must hold (logical AND) for the rule to fire."""

    name: str
    conditions: list[Condition]
    actions: dict[str, Any] = field(default_factory=dict)

    def matches(self, facts: dict[str, Any]) -> bool:
        return all(c.evaluate(facts) for c in self.conditions)


class RuleSet:
    """Evaluates a collection of rules against a fact set."""

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules or []

    def evaluate(self, facts: dict[str, Any]) -> list[Rule]:
        """Return the rules that match, in declaration order."""
        return [r for r in self.rules if r.matches(facts)]

    def collect_actions(self, facts: dict[str, Any]) -> dict[str, Any]:
        """Merge the actions of all matching rules (later rules win on key clash)."""
        result: dict[str, Any] = {}
        for rule in self.evaluate(facts):
            result.update(rule.actions)
        return result
