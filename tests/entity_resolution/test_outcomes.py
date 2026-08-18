from cross_silo_opportunity_engine.config import AUTO_MATCH_THRESHOLD, AUTO_REJECT_THRESHOLD
from cross_silo_opportunity_engine.entity_resolution.outcomes import MatchOutcome, classify


def test_classify_at_or_above_auto_match_threshold():
    assert classify(AUTO_MATCH_THRESHOLD) is MatchOutcome.AUTO_MATCH
    assert classify(1.0) is MatchOutcome.AUTO_MATCH


def test_classify_just_below_auto_match_threshold_is_review():
    assert classify(AUTO_MATCH_THRESHOLD - 0.001) is MatchOutcome.REVIEW_QUEUE


def test_classify_at_or_below_auto_reject_threshold():
    assert classify(AUTO_REJECT_THRESHOLD) is MatchOutcome.AUTO_REJECT
    assert classify(0.0) is MatchOutcome.AUTO_REJECT


def test_classify_just_above_auto_reject_threshold_is_review():
    assert classify(AUTO_REJECT_THRESHOLD + 0.001) is MatchOutcome.REVIEW_QUEUE


def test_classify_mid_range_is_review():
    midpoint = (AUTO_MATCH_THRESHOLD + AUTO_REJECT_THRESHOLD) / 2
    assert classify(midpoint) is MatchOutcome.REVIEW_QUEUE
