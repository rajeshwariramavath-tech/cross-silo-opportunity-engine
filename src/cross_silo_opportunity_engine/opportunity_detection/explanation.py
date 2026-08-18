"""Optional LLM step: narrates a decision the rules already made. Never makes the decision itself."""

from __future__ import annotations

from typing import Any, Protocol


class ExplanationClient(Protocol):
    def complete(self, prompt: str) -> str: ...


def explain_opportunity(
    resolved_match: Any, fired_rules: list[str], client: ExplanationClient
) -> str:
    """Grounded strictly in the matched record's own fields and the rules that fired."""
    raise NotImplementedError
