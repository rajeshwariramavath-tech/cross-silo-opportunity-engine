"""Deterministic, auditable business rules — not a model score, so a flag always has a reason."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Rule:
    name: str
    condition: Callable[[Any], bool]


def evaluate_rules(resolved_match: Any, rules: list[Rule]) -> list[str]:
    """Returns the names of every rule that fired against this match."""
    return [rule.name for rule in rules if rule.condition(resolved_match)]
