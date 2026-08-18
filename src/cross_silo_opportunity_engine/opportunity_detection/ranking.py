"""Ranks qualifying matches by a composite of timing, value, and relationship factors."""

from __future__ import annotations

from typing import Any


def rank_opportunities(flagged_matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(flagged_matches, key=lambda match: match["composite_score"], reverse=True)
