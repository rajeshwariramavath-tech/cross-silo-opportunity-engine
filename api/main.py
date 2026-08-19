"""Stand-in for the sales and debt systems' own internal APIs.

Serves the same rows as data/raw/sales_records.csv and data/raw/debt_records.csv, just over
HTTP as JSON instead of as a file. SalesAPIAdapter and DebtAPIAdapter (in
cross_silo_opportunity_engine.ingestion.adapters.api_adapters) consume these endpoints the
same way they'd consume any real source system's API - ingestion doesn't know or care whether
a record arrived via a CSV file or a network call.

Run with: uvicorn api.main:app --port 8000
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from fastapi import FastAPI

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"

app = FastAPI(title="Cross-Silo Opportunity Engine - Source Systems API")


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@app.get("/sales-records")
def sales_records() -> list[dict[str, Any]]:
    return _read_csv_rows(RAW_DIR / "sales_records.csv")


@app.get("/debt-records")
def debt_records() -> list[dict[str, Any]]:
    return _read_csv_rows(RAW_DIR / "debt_records.csv")
