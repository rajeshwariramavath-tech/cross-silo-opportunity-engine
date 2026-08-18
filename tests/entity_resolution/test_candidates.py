from cross_silo_opportunity_engine.entity_resolution.candidates import generate_candidate_pairs
from cross_silo_opportunity_engine.ingestion.canonical_schema import CanonicalRecord


def _record(system, record_id):
    return CanonicalRecord(source_system=system, source_record_id=record_id, entity_type="client", entity_name=f"Entity {record_id}")


def test_generate_candidate_pairs_only_crosses_sources():
    sales = [_record("sales_records", f"S{i}") for i in range(3)]
    debt = [_record("debt_records", f"D{i}") for i in range(2)]

    pairs = list(generate_candidate_pairs(sales + debt))

    assert len(pairs) == len(sales) * len(debt)
    for record_a, record_b in pairs:
        assert record_a.source_system != record_b.source_system


def test_generate_candidate_pairs_excludes_same_source_pairs():
    same_source = [_record("sales_records", "S1"), _record("sales_records", "S2")]
    assert list(generate_candidate_pairs(same_source)) == []


def test_generate_candidate_pairs_empty_input():
    assert list(generate_candidate_pairs([])) == []
