"""The shared record shape every source adapter normalizes its records into."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CanonicalRecord:
    # source_system + source_record_id are lineage: what makes governance traceability possible later.
    source_system: str
    source_record_id: str
    entity_type: str
    entity_name: str
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    ingested_at: datetime = field(default_factory=datetime.utcnow)
    extra: dict[str, Any] = field(default_factory=dict)
