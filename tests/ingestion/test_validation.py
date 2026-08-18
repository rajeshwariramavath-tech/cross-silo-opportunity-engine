from cross_silo_opportunity_engine.ingestion.canonical_schema import CanonicalRecord
from cross_silo_opportunity_engine.ingestion.validation import validate_record


def _record(**overrides):
    base = dict(source_system="sales_records", source_record_id="SR-1", entity_type="client", entity_name="Acme")
    base.update(overrides)
    return CanonicalRecord(**base)


def test_validate_record_all_required_fields_present():
    result = validate_record(_record())
    assert result.is_valid
    assert result.errors == []


def test_validate_record_missing_entity_name():
    result = validate_record(_record(entity_name=""))
    assert not result.is_valid
    assert result.errors == ["entity_name"]


def test_validate_record_missing_multiple_fields():
    result = validate_record(_record(entity_name="", source_record_id=""))
    assert not result.is_valid
    assert set(result.errors) == {"entity_name", "source_record_id"}
