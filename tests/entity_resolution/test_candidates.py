from cross_silo_opportunity_engine.entity_resolution.candidates import generate_candidate_pairs
from cross_silo_opportunity_engine.ingestion.canonical_schema import CanonicalRecord


def _record(system, record_id, postal_code="80202"):
    return CanonicalRecord(
        source_system=system, source_record_id=record_id, entity_type="client",
        entity_name=f"Entity {record_id}", postal_code=postal_code,
    )


def test_generate_candidate_pairs_only_crosses_sources_within_a_zip_block():
    sales = [_record("sales_records", f"S{i}") for i in range(3)]
    debt = [_record("debt_records", f"D{i}") for i in range(2)]

    pairs = list(generate_candidate_pairs(sales + debt))

    assert len(pairs) == len(sales) * len(debt)
    for record_a, record_b in pairs:
        assert record_a.source_system != record_b.source_system


def test_generate_candidate_pairs_does_not_cross_zip_blocks():
    sales_a = _record("sales_records", "S1", postal_code="80202")
    debt_a = _record("debt_records", "D1", postal_code="80202")
    sales_b = _record("sales_records", "S2", postal_code="33131")
    debt_b = _record("debt_records", "D2", postal_code="33131")

    pairs = list(generate_candidate_pairs([sales_a, debt_a, sales_b, debt_b]))

    ids = {(a.source_record_id, b.source_record_id) for a, b in pairs}
    assert ids == {("S1", "D1"), ("S2", "D2")}


def test_generate_candidate_pairs_uses_only_the_first_five_zip_digits():
    sales = _record("sales_records", "S1", postal_code="94608-1234")
    debt = _record("debt_records", "D1", postal_code="94608")

    pairs = list(generate_candidate_pairs([sales, debt]))

    assert len(pairs) == 1


def test_generate_candidate_pairs_skips_records_with_no_postal_code():
    sales = _record("sales_records", "S1", postal_code=None)
    debt = _record("debt_records", "D1", postal_code="80202")

    assert list(generate_candidate_pairs([sales, debt])) == []


def test_generate_candidate_pairs_excludes_same_source_pairs_within_a_block():
    same_source = [_record("sales_records", "S1"), _record("sales_records", "S2")]
    assert list(generate_candidate_pairs(same_source)) == []


def test_generate_candidate_pairs_empty_input():
    assert list(generate_candidate_pairs([])) == []
