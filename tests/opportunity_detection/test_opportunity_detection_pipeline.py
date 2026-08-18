from datetime import date

from opportunity_detection import _parse_currency, _parse_date, build_opportunity, run_opportunity_detection


def test_parse_currency_handles_dollar_sign_and_commas():
    assert _parse_currency("$1,850,000") == 1850000.0


def test_parse_currency_handles_plain_number_string():
    assert _parse_currency("4200000") == 4200000.0


def test_parse_currency_empty_or_invalid_is_none():
    assert _parse_currency("") is None
    assert _parse_currency("not a number") is None


def test_parse_date_valid_iso():
    assert _parse_date("2029-01-10") == date(2029, 1, 10)


def test_parse_date_invalid_format_is_none():
    assert _parse_date("01/10/2029") is None
    assert _parse_date("") is None


def _canonical_row(source_system, source_id, entity_name, **extra):
    row = {
        "source_system": source_system, "source_record_id": source_id, "entity_name": entity_name,
        "extra_sale_price": "", "extra_close_date": "", "extra_broker_name": "", "extra_property_type": "",
        "extra_loan_amount": "", "extra_orig_date": "", "extra_maturity_date": "", "extra_lender_name": "",
        "extra_loan_type": "", "extra_notes": "",
    }
    row.update(extra)
    return row


def test_build_opportunity_merges_sales_and_debt_sides():
    lookup = {
        ("sales_records", "SR-1"): _canonical_row("sales_records", "SR-1", "Acme", extra_sale_price="7000000"),
        ("debt_records", "DBT-1"): _canonical_row(
            "debt_records", "DBT-1", "Acme LLC", extra_loan_amount="3000000", extra_notes="past due 30 days"
        ),
    }
    match = {
        "source_system_a": "sales_records", "source_id_a": "SR-1",
        "source_system_b": "debt_records", "source_id_b": "DBT-1", "confidence": "0.98",
    }

    opportunity = build_opportunity(match, lookup)

    assert opportunity["entity_name"] == "Acme"
    assert opportunity["sale_price"] == "7000000"
    assert opportunity["loan_amount"] == "3000000"
    assert opportunity["_sale_value"] == 7000000.0
    assert opportunity["_loan_value"] == 3000000.0
    assert opportunity["_notes_lower"] == "past due 30 days"


def test_build_opportunity_missing_lookup_returns_none():
    match = {
        "source_system_a": "sales_records", "source_id_a": "SR-missing",
        "source_system_b": "debt_records", "source_id_b": "DBT-missing", "confidence": "0.9",
    }
    assert build_opportunity(match, {}) is None


def test_past_due_loan_fires_urgency_rule_even_under_value_threshold():
    lookup = {
        ("sales_records", "SR-1"): _canonical_row("sales_records", "SR-1", "Acme", extra_sale_price="1000000"),
        ("debt_records", "DBT-1"): _canonical_row(
            "debt_records", "DBT-1", "Acme LLC",
            extra_loan_amount="500000", extra_maturity_date="2099-01-01", extra_notes="past due 30 days",
        ),
    }
    match = {
        "source_system_a": "sales_records", "source_id_a": "SR-1",
        "source_system_b": "debt_records", "source_id_b": "DBT-1", "confidence": "0.5",
    }

    opportunities = run_opportunity_detection([match], lookup, today=date(2026, 1, 1))

    assert len(opportunities) == 1
    assert "loan_past_due" in opportunities[0]["fired_rules"]
    assert "high_value_deal" not in opportunities[0]["fired_rules"]


def test_no_rules_fire_excludes_the_match():
    lookup = {
        ("sales_records", "SR-1"): _canonical_row("sales_records", "SR-1", "Acme", extra_sale_price="100"),
        ("debt_records", "DBT-1"): _canonical_row(
            "debt_records", "DBT-1", "Acme LLC", extra_loan_amount="100", extra_maturity_date="2099-01-01"
        ),
    }
    match = {
        "source_system_a": "sales_records", "source_id_a": "SR-1",
        "source_system_b": "debt_records", "source_id_b": "DBT-1", "confidence": "0.5",
    }

    assert run_opportunity_detection([match], lookup, today=date(2026, 1, 1)) == []
