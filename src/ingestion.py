"""Stage 1 — ingestion & normalization, runnable end to end.

Reads data/raw/sales_records.csv and data/raw/debt_records.csv (two source systems with no
shared key and different address shapes), normalizes each into the shared CanonicalRecord
schema, and writes:

- data/processed/canonical_records.csv  — valid records, ready for entity resolution
- data/processed/ingestion_rejects.csv  — invalid records, flagged and kept rather than dropped

Every row in both outputs carries source_system + source_record_id so any downstream value
can be traced back to the exact record it came from.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cross_silo_opportunity_engine.ingestion.adapters.base import BaseSourceAdapter
from cross_silo_opportunity_engine.ingestion.adapters.csv_adapters import DebtCSVAdapter, SalesCSVAdapter
from cross_silo_opportunity_engine.ingestion.canonical_schema import CanonicalRecord
from cross_silo_opportunity_engine.ingestion.validation import validate_record

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"

SALES_REQUIRED_RAW_FIELDS = ["client_name", "property_address", "sale_price", "close_date"]
DEBT_REQUIRED_RAW_FIELDS = ["borrower_name", "property_addr", "loan_amount", "orig_date"]

# Business-specific fields don't fit one shared schema across lines of business, so they're
# carried through verbatim in CanonicalRecord.extra rather than forced into common columns.
EXTRA_FIELDNAMES = [
    "sale_price", "close_date", "broker_name", "property_type",
    "loan_amount", "orig_date", "maturity_date", "lender_name", "loan_type", "notes",
]

CANONICAL_FIELDNAMES = [
    "source_system", "source_record_id", "entity_type", "entity_name",
    "address_line1", "address_line2", "city", "state", "postal_code",
    "latitude", "longitude", "ingested_at",
] + [f"extra_{name}" for name in EXTRA_FIELDNAMES]

REJECT_FIELDNAMES = ["source_system", "source_record_id", "entity_name", "reason", "raw_record"]


def _missing_raw_fields(raw_record: dict[str, Any], required_fields: list[str]) -> list[str]:
    return [f"missing {field}" for field in required_fields if not (raw_record.get(field) or "").strip()]


def _canonical_row(record: CanonicalRecord) -> dict[str, Any]:
    row: dict[str, Any] = {
        "source_system": record.source_system,
        "source_record_id": record.source_record_id,
        "entity_type": record.entity_type,
        "entity_name": record.entity_name,
        "address_line1": record.address_line1,
        "address_line2": record.address_line2,
        "city": record.city,
        "state": record.state,
        "postal_code": record.postal_code,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "ingested_at": record.ingested_at.isoformat(),
    }
    for name in EXTRA_FIELDNAMES:
        row[f"extra_{name}"] = record.extra.get(name, "")
    return row


def run_ingestion(
    adapters: list[tuple[BaseSourceAdapter, list[str]]],
) -> tuple[list[CanonicalRecord], list[dict[str, Any]]]:
    """Runs every adapter and splits its output into (valid_records, rejected_rows)."""
    valid_records: list[CanonicalRecord] = []
    rejected_rows: list[dict[str, Any]] = []

    for adapter, required_raw_fields in adapters:
        for raw_record in adapter.read():
            record = adapter.to_canonical(raw_record)
            reasons = _missing_raw_fields(raw_record, required_raw_fields)
            reasons += validate_record(record).errors

            if reasons:
                rejected_rows.append(
                    {
                        "source_system": record.source_system,
                        "source_record_id": record.source_record_id,
                        "entity_name": record.entity_name,
                        "reason": "; ".join(reasons),
                        "raw_record": json.dumps(raw_record, ensure_ascii=False),
                    }
                )
            else:
                valid_records.append(record)

    return valid_records, rejected_rows


def write_canonical_records(records: list[CanonicalRecord], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANONICAL_FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(_canonical_row(record))


def write_rejects(rejected_rows: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REJECT_FIELDNAMES)
        writer.writeheader()
        for row in rejected_rows:
            writer.writerow(row)


def build_adapters(source: str, api_base_url: str) -> list[tuple[BaseSourceAdapter, list[str]]]:
    """CSV and API adapters are interchangeable here on purpose: both produce identical
    CanonicalRecords, so nothing downstream of run_ingestion() needs to know or care which
    one ran."""
    if source == "csv":
        return [
            (SalesCSVAdapter(RAW_DIR / "sales_records.csv"), SALES_REQUIRED_RAW_FIELDS),
            (DebtCSVAdapter(RAW_DIR / "debt_records.csv"), DEBT_REQUIRED_RAW_FIELDS),
        ]

    # Imported lazily so a CSV-only install never needs the optional "requests" dependency.
    from cross_silo_opportunity_engine.ingestion.adapters.api_adapters import DebtAPIAdapter, SalesAPIAdapter

    return [
        (SalesAPIAdapter(api_base_url), SALES_REQUIRED_RAW_FIELDS),
        (DebtAPIAdapter(api_base_url), DEBT_REQUIRED_RAW_FIELDS),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", choices=["csv", "api"], default="csv",
        help="Read from data/raw/*.csv directly (default) or from the FastAPI app in api/main.py.",
    )
    parser.add_argument(
        "--api-base-url", default=DEFAULT_API_BASE_URL,
        help=f"Base URL for --source api (default: {DEFAULT_API_BASE_URL}).",
    )
    args = parser.parse_args()

    adapters = build_adapters(args.source, args.api_base_url)
    valid_records, rejected_rows = run_ingestion(adapters)
    write_canonical_records(valid_records, PROCESSED_DIR / "canonical_records.csv")
    write_rejects(rejected_rows, PROCESSED_DIR / "ingestion_rejects.csv")
    print(f"source: {args.source}, canonical records: {len(valid_records)}, rejected: {len(rejected_rows)}")


if __name__ == "__main__":
    main()
