import pytest

from cross_silo_opportunity_engine.entity_resolution.signals import (
    address_similarity,
    geographic_proximity,
    name_similarity,
)
from cross_silo_opportunity_engine.ingestion.canonical_schema import CanonicalRecord


def _record(**overrides):
    base = dict(
        source_system="test",
        source_record_id="1",
        entity_type="client",
        entity_name="Acme Group",
        address_line1="123 Main Street",
        city="Denver",
        state="CO",
        postal_code="80202",
    )
    base.update(overrides)
    return CanonicalRecord(**base)


def test_address_similarity_identical_is_one():
    a = _record()
    b = _record(source_record_id="2")
    assert address_similarity(a, b) == pytest.approx(1.0, abs=1e-4)


def test_address_similarity_missing_line1_is_zero():
    a = _record()
    b = _record(address_line1=None)
    assert address_similarity(a, b) == 0.0


def test_address_similarity_different_address_is_low():
    a = _record()
    b = _record(address_line1="999 Oak Avenue", city="Miami", state="FL", postal_code="33131")
    assert address_similarity(a, b) < 0.3


def test_name_similarity_legal_suffix_difference_scores_high():
    a = _record(entity_name="Silverline Capital")
    b = _record(entity_name="Silverline Capital LLC")
    assert name_similarity(a, b) > 0.9


def test_name_similarity_different_names_scores_low():
    a = _record(entity_name="Silverline Capital")
    b = _record(entity_name="Falcon Creek Holdings")
    assert name_similarity(a, b) < 0.3


def test_name_similarity_missing_name_is_zero():
    a = _record()
    b = _record(entity_name="")
    assert name_similarity(a, b) == 0.0


def test_geographic_proximity_none_when_coordinates_missing():
    assert geographic_proximity(_record(), _record()) is None


def test_geographic_proximity_same_point_is_high():
    a = _record(latitude=39.7392, longitude=-104.9903)
    b = _record(latitude=39.7392, longitude=-104.9903)
    assert geographic_proximity(a, b) == pytest.approx(1.0, abs=1e-4)


def test_geographic_proximity_far_apart_clamps_to_zero():
    denver = _record(latitude=39.7392, longitude=-104.9903)
    nyc = _record(latitude=40.7128, longitude=-74.0060)
    assert geographic_proximity(denver, nyc) == 0.0
