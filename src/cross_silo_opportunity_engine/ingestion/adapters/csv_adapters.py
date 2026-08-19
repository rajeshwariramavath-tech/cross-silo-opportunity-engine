"""CSV adapters for the two source systems: read straight from data/raw/*.csv."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterator

from ..canonical_schema import CanonicalRecord
from ..normalization import normalize_address, normalize_entity_name, normalize_state, split_combined_address
from .base import BaseSourceAdapter


class _SalesRecordMixin:
    """to_canonical for the sales source - shared by SalesCSVAdapter and SalesAPIAdapter,
    since the raw record shape is identical whether it arrived as a CSV row or a JSON row."""

    source_system = "sales_records"

    def to_canonical(self, raw_record: dict[str, Any]) -> CanonicalRecord:
        address = normalize_address(raw_record.get("property_address", ""))
        return CanonicalRecord(
            source_system=self.source_system,
            source_record_id=raw_record.get("deal_id", ""),
            entity_type="client",
            entity_name=normalize_entity_name(raw_record.get("client_name", "")),
            address_line1=address["address_line1"],
            address_line2=address["address_line2"],
            city=(raw_record.get("city") or "").strip() or None,
            state=normalize_state(raw_record.get("state", "")),
            postal_code=(raw_record.get("zip") or "").strip() or None,
            extra={
                "sale_price": raw_record.get("sale_price", ""),
                "close_date": raw_record.get("close_date", ""),
                "broker_name": raw_record.get("broker_name", ""),
                "property_type": raw_record.get("property_type", ""),
            },
        )


class _DebtRecordMixin:
    """to_canonical for the debt source - shared by DebtCSVAdapter and DebtAPIAdapter."""

    source_system = "debt_records"

    def to_canonical(self, raw_record: dict[str, Any]) -> CanonicalRecord:
        address = split_combined_address(raw_record.get("property_addr", ""))
        return CanonicalRecord(
            source_system=self.source_system,
            source_record_id=raw_record.get("loan_ref", ""),
            entity_type="borrower",
            entity_name=normalize_entity_name(raw_record.get("borrower_name", "")),
            address_line1=address["address_line1"],
            address_line2=address["address_line2"],
            city=address["city"],
            state=address["state"],
            postal_code=address["postal_code"],
            extra={
                "loan_amount": raw_record.get("loan_amount", ""),
                "orig_date": raw_record.get("orig_date", ""),
                "maturity_date": raw_record.get("maturity_date", ""),
                "lender_name": raw_record.get("lender_name", ""),
                "loan_type": raw_record.get("loan_type", ""),
                "notes": raw_record.get("notes", ""),
            },
        )


class SalesCSVAdapter(_SalesRecordMixin, BaseSourceAdapter):
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path

    def read(self) -> Iterator[dict[str, Any]]:
        with self.csv_path.open(newline="", encoding="utf-8") as handle:
            yield from csv.DictReader(handle)


class DebtCSVAdapter(_DebtRecordMixin, BaseSourceAdapter):
    def __init__(self, csv_path: Path):
        self.csv_path = csv_path

    def read(self) -> Iterator[dict[str, Any]]:
        with self.csv_path.open(newline="", encoding="utf-8") as handle:
            yield from csv.DictReader(handle)
