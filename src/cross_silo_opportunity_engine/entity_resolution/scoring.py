"""Combines independent signal scores into one weighted confidence score."""

from __future__ import annotations

from ..config import ENTITY_RESOLUTION_SIGNAL_WEIGHTS


def compute_confidence(signal_scores: dict[str, float]) -> float:
    raise NotImplementedError
