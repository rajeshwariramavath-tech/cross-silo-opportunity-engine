from pathlib import Path

from cross_silo_opportunity_engine.ingestion.adapters.base import BaseSourceAdapter
from cross_silo_opportunity_engine.ingestion.canonical_schema import CanonicalRecord

from ingestion import DebtCSVAdapter, SalesCSVAdapter, _missing_raw_fields, run_ingestion


def test_sales_adapter_to_canonical_normalizes_and_preserves_lineage():
    adapter = SalesCSVAdapter(Path("unused.csv"))
    raw = {
        "deal_id": "SR-9001",
        "client_name": "ashford commercial grp",
        "property_address": "2200 Airport Rd, Suite 5",
        "city": "Nashville",
        "state": "tn",
        "zip": "37217",
        "sale_price": "6250000",
        "close_date": "2024-05-03",
        "broker_name": "Priya Nair",
        "property_type": "Industrial",
    }

    record = adapter.to_canonical(raw)

    assert record.source_system == "sales_records"
    assert record.source_record_id == "SR-9001"
    assert record.entity_type == "client"
    assert record.entity_name == "Ashford Commercial Group"
    assert record.address_line1 == "2200 Airport Road"
    assert record.address_line2 == "Suite 5"
    assert record.state == "TN"
    assert record.extra["sale_price"] == "6250000"


def test_debt_adapter_to_canonical_splits_combined_address():
    adapter = DebtCSVAdapter(Path("unused.csv"))
    raw = {
        "loan_ref": "DBT-9001",
        "borrower_name": "Ashford Commercial Grp",
        "property_addr": "2200 Airport Road Ste 5, Nashville,TN 37217",
        "loan_amount": "3950000",
        "orig_date": "2024-03-11",
        "maturity_date": "2029-03-11",
        "lender_name": "Volunteer State Bank",
        "loan_type": "Construction Loan",
        "notes": "",
    }

    record = adapter.to_canonical(raw)

    assert record.source_system == "debt_records"
    assert record.entity_type == "borrower"
    assert record.address_line1 == "2200 Airport Road"
    assert record.address_line2 == "Suite 5"
    assert record.city == "Nashville"
    assert record.state == "TN"
    assert record.postal_code == "37217"


def test_missing_raw_fields_reports_blank_required_fields():
    reasons = _missing_raw_fields({"a": "", "b": "x", "c": "   "}, ["a", "b", "c"])
    assert reasons == ["missing a", "missing c"]


class _FakeAdapter(BaseSourceAdapter):
    source_system = "fake_source"

    def __init__(self, rows):
        self._rows = rows

    def read(self):
        yield from self._rows

    def to_canonical(self, raw_record):
        return CanonicalRecord(
            source_system=self.source_system,
            source_record_id=raw_record["id"],
            entity_type="client",
            entity_name=raw_record.get("name", ""),
            address_line1=raw_record.get("address") or None,
        )


def test_run_ingestion_splits_valid_and_rejected_rows():
    good_row = {"id": "1", "name": "Acme", "address": "1 Main St", "value": "100"}
    bad_row = {"id": "2", "name": "Beta", "address": "", "value": ""}
    adapter = _FakeAdapter([good_row, bad_row])

    valid, rejected = run_ingestion([(adapter, ["address", "value"])])

    assert len(valid) == 1
    assert valid[0].source_record_id == "1"

    assert len(rejected) == 1
    assert rejected[0]["source_record_id"] == "2"
    assert rejected[0]["source_system"] == "fake_source"
    assert "missing address" in rejected[0]["reason"]
    assert "missing value" in rejected[0]["reason"]
