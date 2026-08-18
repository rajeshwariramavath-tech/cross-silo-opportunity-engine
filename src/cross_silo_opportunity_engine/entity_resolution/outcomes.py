"""Three-outcome routing: confidence maps to auto-match, review queue, or auto-reject."""

from __future__ import annotations

from enum import Enum

from ..config import AUTO_MATCH_THRESHOLD, AUTO_REJECT_THRESHOLD


class MatchOutcome(Enum):
    AUTO_MATCH = "auto_match"
    REVIEW_QUEUE = "review_queue"
    AUTO_REJECT = "auto_reject"


def classify(confidence: float) -> MatchOutcome:
    if confidence >= AUTO_MATCH_THRESHOLD:
        return MatchOutcome.AUTO_MATCH
    if confidence <= AUTO_REJECT_THRESHOLD:
        return MatchOutcome.AUTO_REJECT
    return MatchOutcome.REVIEW_QUEUE
