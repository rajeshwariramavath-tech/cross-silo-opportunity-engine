import csv

from cross_silo_opportunity_engine.entity_resolution.outcomes import MatchOutcome
from cross_silo_opportunity_engine.ingestion.canonical_schema import CanonicalRecord

from entity_resolution import load_canonical_records, run_entity_resolution, score_pair


def _record(system, record_id, name, address_line1, city="Denver", state="CO", postal_code="80202"):
    return CanonicalRecord(
        source_system=system,
        source_record_id=record_id,
        entity_type="client",
        entity_name=name,
        address_line1=address_line1,
        city=city,
        state=state,
        postal_code=postal_code,
    )


def test_score_pair_matching_entity_auto_matches():
    a = _record("sales_records", "S1", "Silverline Capital", "900 Congress Avenue")
    b = _record("debt_records", "D1", "Silverline Capital LLC", "900 Congress Avenue")
    result = score_pair(a, b)
    assert result["outcome"] == MatchOutcome.AUTO_MATCH.value
    assert result["confidence"] > 0.9


def test_score_pair_unrelated_entities_auto_rejects():
    a = _record("sales_records", "S1", "Silverline Capital", "900 Congress Avenue")
    b = _record("debt_records", "D2", "Falcon Creek Holdings", "1801 California Street", city="Miami", state="FL", postal_code="33131")
    result = score_pair(a, b)
    assert result["outcome"] == MatchOutcome.AUTO_REJECT.value


def test_run_entity_resolution_sorts_by_confidence_descending():
    records = [
        _record("sales_records", "S1", "Silverline Capital", "900 Congress Avenue"),
        _record("debt_records", "D1", "Silverline Capital LLC", "900 Congress Avenue"),
        # A second zip block, so this pair is actually blocked and scored too - not just a
        # lone unmatched record blocking would otherwise skip entirely.
        _record("sales_records", "S2", "Nowhere Retail Partners", "1 Nowhere Road", city="Miami", state="FL", postal_code="33131"),
        _record("debt_records", "D2", "Totally Unrelated Co", "42 Somewhere Else Blvd", city="Miami", state="FL", postal_code="33131"),
    ]
    matches = run_entity_resolution(records)
    assert len(matches) == 2  # one pair per zip block (80202, 33131) - blocking keeps them from cross-pairing
    confidences = [match["confidence"] for match in matches]
    assert confidences == sorted(confidences, reverse=True)


def test_load_canonical_records_round_trips_csv(tmp_path):
    csv_path = tmp_path / "canonical_records.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_system", "source_record_id", "entity_type", "entity_name",
                "address_line1", "address_line2", "city", "state", "postal_code",
                "latitude", "longitude", "ingested_at",
            ],
        )
        writer.writeheader()
        writer.writerow({
            "source_system": "sales_records", "source_record_id": "SR-1", "entity_type": "client",
            "entity_name": "Acme", "address_line1": "1 Main St", "address_line2": "",
            "city": "Denver", "state": "CO", "postal_code": "80202",
            "latitude": "", "longitude": "", "ingested_at": "2024-01-01T00:00:00",
        })

    records = load_canonical_records(csv_path)

    assert len(records) == 1
    record = records[0]
    assert record.entity_name == "Acme"
    assert record.address_line2 is None
    assert record.latitude is None
