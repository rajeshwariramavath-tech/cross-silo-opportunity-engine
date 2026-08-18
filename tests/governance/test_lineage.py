from cross_silo_opportunity_engine.governance.lineage import trace_field


def _opportunity():
    return {
        "sales_source_system": "sales_records", "sales_source_id": "SR-1",
        "debt_source_system": "debt_records", "debt_source_id": "DBT-1",
    }


def test_sales_field_traces_to_sales_record_only():
    assert trace_field(_opportunity(), "sale_price") == [{"source_system": "sales_records", "source_id": "SR-1"}]


def test_debt_field_traces_to_debt_record_only():
    assert trace_field(_opportunity(), "loan_amount") == [{"source_system": "debt_records", "source_id": "DBT-1"}]


def test_derived_field_traces_to_both_records():
    assert trace_field(_opportunity(), "composite_score") == [
        {"source_system": "sales_records", "source_id": "SR-1"},
        {"source_system": "debt_records", "source_id": "DBT-1"},
    ]


def test_unknown_field_traces_to_nothing():
    assert trace_field(_opportunity(), "not_a_real_field") == []
