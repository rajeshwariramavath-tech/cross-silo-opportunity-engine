import pytest

from cross_silo_opportunity_engine.config import ENTITY_RESOLUTION_SIGNAL_WEIGHTS
from cross_silo_opportunity_engine.entity_resolution.scoring import compute_confidence


def test_compute_confidence_with_all_signals_present():
    scores = {"address_similarity": 0.8, "name_similarity": 0.6, "geographic_proximity": 1.0}
    expected = sum(ENTITY_RESOLUTION_SIGNAL_WEIGHTS[name] * value for name, value in scores.items())
    assert compute_confidence(scores) == pytest.approx(expected, abs=1e-4)


def test_compute_confidence_renormalizes_when_a_signal_is_missing():
    # geographic_proximity is routinely None (no coordinates) - its absence must not just
    # zero out that share of the weight, or every pair would be silently deflated.
    scores = {"address_similarity": 0.8, "name_similarity": 0.6, "geographic_proximity": None}
    w = ENTITY_RESOLUTION_SIGNAL_WEIGHTS
    total_weight = w["address_similarity"] + w["name_similarity"]
    expected = (w["address_similarity"] * 0.8 + w["name_similarity"] * 0.6) / total_weight
    assert compute_confidence(scores) == pytest.approx(expected, abs=1e-4)


def test_compute_confidence_all_signals_missing_is_zero():
    scores = {"address_similarity": None, "name_similarity": None, "geographic_proximity": None}
    assert compute_confidence(scores) == 0.0


def test_compute_confidence_ignores_unknown_signal_keys():
    scores = {"address_similarity": 1.0, "name_similarity": 1.0, "geographic_proximity": None, "mystery_signal": 0.9}
    assert compute_confidence(scores) == pytest.approx(1.0, abs=1e-4)
