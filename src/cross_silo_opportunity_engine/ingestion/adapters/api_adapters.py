"""API adapters for the two source systems: read from the FastAPI app in api/main.py instead
of the CSV files directly. to_canonical is identical to the CSV adapters (same mixins) - only
read() differs, which is the whole point: ingestion, entity resolution, opportunity detection,
and governance only ever see CanonicalRecords, so they don't care which adapter produced them.
"""

from __future__ import annotations

from typing import Any, Iterator

import requests

from .base import BaseSourceAdapter
from .csv_adapters import _DebtRecordMixin, _SalesRecordMixin


class SalesAPIAdapter(_SalesRecordMixin, BaseSourceAdapter):
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def read(self) -> Iterator[dict[str, Any]]:
        response = requests.get(f"{self.base_url}/sales-records", timeout=self.timeout)
        response.raise_for_status()
        yield from response.json()


class DebtAPIAdapter(_DebtRecordMixin, BaseSourceAdapter):
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def read(self) -> Iterator[dict[str, Any]]:
        response = requests.get(f"{self.base_url}/debt-records", timeout=self.timeout)
        response.raise_for_status()
        yield from response.json()
