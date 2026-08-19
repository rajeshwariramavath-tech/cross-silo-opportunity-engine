from cross_silo_opportunity_engine.ingestion.adapters.api_adapters import DebtAPIAdapter, SalesAPIAdapter
from cross_silo_opportunity_engine.ingestion.adapters.csv_adapters import DebtCSVAdapter, SalesCSVAdapter


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_sales_api_adapter_reads_from_the_expected_url(monkeypatch):
    requested_urls = []

    def fake_get(url, timeout):
        requested_urls.append(url)
        return _FakeResponse([{"deal_id": "SR-1"}])

    monkeypatch.setattr("cross_silo_opportunity_engine.ingestion.adapters.api_adapters.requests.get", fake_get)

    adapter = SalesAPIAdapter("http://127.0.0.1:8000/")
    rows = list(adapter.read())

    assert requested_urls == ["http://127.0.0.1:8000/sales-records"]
    assert rows == [{"deal_id": "SR-1"}]


def test_debt_api_adapter_reads_from_the_expected_url(monkeypatch):
    requested_urls = []

    def fake_get(url, timeout):
        requested_urls.append(url)
        return _FakeResponse([{"loan_ref": "DBT-1"}])

    monkeypatch.setattr("cross_silo_opportunity_engine.ingestion.adapters.api_adapters.requests.get", fake_get)

    adapter = DebtAPIAdapter("http://127.0.0.1:8000")
    rows = list(adapter.read())

    assert requested_urls == ["http://127.0.0.1:8000/debt-records"]
    assert rows == [{"loan_ref": "DBT-1"}]


def test_sales_api_and_csv_adapters_produce_identical_canonical_records(monkeypatch):
    # Same to_canonical mixin either way - this pins that the API path can't silently diverge
    # from the CSV path's normalization.
    raw_row = {
        "deal_id": "SR-1003", "client_name": "Silverline Capital",
        "property_address": "900 Congress Ave Fl 12", "city": "Austin", "state": "TX", "zip": "78701",
        "sale_price": "7600000", "close_date": "March 22, 2024", "broker_name": "", "property_type": "Office",
    }

    def fake_get(url, timeout):
        return _FakeResponse([raw_row])

    monkeypatch.setattr("cross_silo_opportunity_engine.ingestion.adapters.api_adapters.requests.get", fake_get)

    api_record = SalesAPIAdapter("http://127.0.0.1:8000").to_canonical(raw_row)
    csv_record = SalesCSVAdapter("unused.csv").to_canonical(raw_row)

    assert api_record.entity_name == csv_record.entity_name
    assert api_record.address_line1 == csv_record.address_line1
    assert api_record.address_line2 == csv_record.address_line2
    assert api_record.extra == csv_record.extra


def test_debt_api_and_csv_adapters_produce_identical_canonical_records(monkeypatch):
    raw_row = {
        "loan_ref": "DBT-2024-003", "borrower_name": "Silverline Capital LLC",
        "property_addr": "900 Congress Avenue, 12th Floor, Austin, TX 78701",
        "loan_amount": "4900000", "orig_date": "03/01/2024", "maturity_date": "2031-03-01",
        "lender_name": "Republic Trust Bank", "loan_type": "Term Loan", "notes": "past due 30 days",
    }

    def fake_get(url, timeout):
        return _FakeResponse([raw_row])

    monkeypatch.setattr("cross_silo_opportunity_engine.ingestion.adapters.api_adapters.requests.get", fake_get)

    api_record = DebtAPIAdapter("http://127.0.0.1:8000").to_canonical(raw_row)
    csv_record = DebtCSVAdapter("unused.csv").to_canonical(raw_row)

    assert api_record.entity_name == csv_record.entity_name
    assert api_record.address_line1 == csv_record.address_line1
    assert api_record.city == csv_record.city
    assert api_record.extra == csv_record.extra
