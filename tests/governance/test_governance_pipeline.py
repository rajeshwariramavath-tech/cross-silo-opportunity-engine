import csv

import pytest

from cross_silo_opportunity_engine.governance.roles import Role

from governance import get_opportunities_for_role, load_opportunities


def test_get_opportunities_for_role_applies_scoping_per_role():
    opportunities = [{
        "entity_name": "Acme", "property_type": "Office",
        "sale_price": "1000000", "loan_amount": "500000", "notes": "",
        "fired_rules": ["high_value_deal"], "composite_score": 2,
        "sales_source_system": "sales_records", "sales_source_id": "SR-1",
        "debt_source_system": "debt_records", "debt_source_id": "DBT-1",
    }]

    scoped = get_opportunities_for_role(opportunities, Role.PROPERTY_MANAGEMENT)

    assert len(scoped) == 1
    assert set(scoped[0].keys()) == {
        "entity_name", "property_type",
        "sales_source_system", "sales_source_id", "debt_source_system", "debt_source_id",
    }


def test_load_opportunities_coerces_types(tmp_path):
    csv_path = tmp_path / "opportunities.csv"
    fieldnames = [
        "entity_name", "sales_source_system", "sales_source_id", "debt_source_system", "debt_source_id",
        "sale_price", "close_date", "broker_name", "property_type",
        "loan_amount", "orig_date", "maturity_date", "lender_name", "loan_type", "notes",
        "entity_resolution_confidence", "fired_rules", "composite_score", "rationale",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "entity_name": "Acme", "sales_source_system": "sales_records", "sales_source_id": "SR-1",
            "debt_source_system": "debt_records", "debt_source_id": "DBT-1",
            "sale_price": "1000000", "close_date": "", "broker_name": "", "property_type": "Office",
            "loan_amount": "500000", "orig_date": "", "maturity_date": "", "lender_name": "", "loan_type": "",
            "notes": "", "entity_resolution_confidence": "0.98",
            "fired_rules": "high_value_deal; strong_relationship_match", "composite_score": "3", "rationale": "",
        })

    opportunities = load_opportunities(csv_path)

    assert len(opportunities) == 1
    row = opportunities[0]
    assert row["composite_score"] == 3
    assert row["entity_resolution_confidence"] == pytest.approx(0.98)
    assert row["fired_rules"] == ["high_value_deal", "strong_relationship_match"]


def test_load_opportunities_handles_no_fired_rules(tmp_path):
    csv_path = tmp_path / "opportunities.csv"
    fieldnames = [
        "entity_name", "sales_source_system", "sales_source_id", "debt_source_system", "debt_source_id",
        "sale_price", "close_date", "broker_name", "property_type",
        "loan_amount", "orig_date", "maturity_date", "lender_name", "loan_type", "notes",
        "entity_resolution_confidence", "fired_rules", "composite_score", "rationale",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({name: "" for name in fieldnames})

    row = load_opportunities(csv_path)[0]
    assert row["fired_rules"] == []
    assert row["composite_score"] is None
    assert row["entity_resolution_confidence"] is None
