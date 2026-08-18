"""Combines independent signal scores into one weighted confidence score."""

from __future__ import annotations

from ..config import ENTITY_RESOLUTION_SIGNAL_WEIGHTS


def compute_confidence(signal_scores: dict[str, float | None]) -> float:
    # Missing signals (e.g. geographic_proximity with no coordinates) are excluded and the
    # remaining weights renormalized, rather than treated as zero - an optional signal being
    # absent shouldn't silently deflate every pair's confidence.
    present = {
        name: score
        for name, score in signal_scores.items()
        if score is not None and name in ENTITY_RESOLUTION_SIGNAL_WEIGHTS
    }
    if not present:
        return 0.0
    total_weight = sum(ENTITY_RESOLUTION_SIGNAL_WEIGHTS[name] for name in present)
    weighted_sum = sum(ENTITY_RESOLUTION_SIGNAL_WEIGHTS[name] * score for name, score in present.items())
    return round(weighted_sum / total_weight, 4)
