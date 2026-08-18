"""Independent similarity signals compared between two candidate records."""

from __future__ import annotations

from ..ingestion.canonical_schema import CanonicalRecord


def address_similarity(a: CanonicalRecord, b: CanonicalRecord) -> float:
    raise NotImplementedError


def name_similarity(a: CanonicalRecord, b: CanonicalRecord) -> float:
    raise NotImplementedError


def geographic_proximity(a: CanonicalRecord, b: CanonicalRecord) -> float | None:
    """None when either record lacks coordinates — this signal is optional."""
    raise NotImplementedError
