import csv
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import RAW_DIR, app

client = TestClient(app)


def _expected_rows(csv_path: Path):
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_sales_records_endpoint_matches_the_csv_file():
    response = client.get("/sales-records")
    assert response.status_code == 200

    rows = response.json()
    expected = _expected_rows(RAW_DIR / "sales_records.csv")
    assert len(rows) == len(expected)
    assert len(rows) > 0
    assert rows[0] == expected[0]


def test_debt_records_endpoint_matches_the_csv_file():
    response = client.get("/debt-records")
    assert response.status_code == 200

    rows = response.json()
    expected = _expected_rows(RAW_DIR / "debt_records.csv")
    assert len(rows) == len(expected)
    assert len(rows) > 0
    assert rows[0] == expected[0]
