"""Independent similarity signals compared between two candidate records."""

from __future__ import annotations

from difflib import SequenceMatcher

from ..ingestion.canonical_schema import CanonicalRecord

# Pure legal-entity-type tokens are stripped for the "core name" comparison since they
# legitimately differ across systems (one side's "LLC" vs the other's bare name) without
# meaning the entity is different. Words like "Trust"/"Group"/"Fund" are left alone because
# they carry real distinguishing meaning between otherwise-similar company names.
_LEGAL_SUFFIX_TOKENS = {"llc", "inc", "lp", "llp", "reit", "corp", "co"}


def _zip5(postal_code: str) -> str:
    return postal_code.strip()[:5]


def _core_name(name: str) -> str:
    tokens = [token for token in name.lower().split() if token not in _LEGAL_SUFFIX_TOKENS]
    return " ".join(tokens)


def address_similarity(a: CanonicalRecord, b: CanonicalRecord) -> float:
    if not a.address_line1 or not b.address_line1:
        return 0.0
    line1_score = SequenceMatcher(None, a.address_line1.lower(), b.address_line1.lower()).ratio()
    zip_score = (
        1.0 if a.postal_code and b.postal_code and _zip5(a.postal_code) == _zip5(b.postal_code) else 0.0
    )
    city_score = 1.0 if a.city and b.city and a.city.strip().lower() == b.city.strip().lower() else 0.0
    return round(0.6 * line1_score + 0.25 * zip_score + 0.15 * city_score, 4)


def name_similarity(a: CanonicalRecord, b: CanonicalRecord) -> float:
    if not a.entity_name or not b.entity_name:
        return 0.0
    full_score = SequenceMatcher(None, a.entity_name.lower(), b.entity_name.lower()).ratio()
    core_score = SequenceMatcher(None, _core_name(a.entity_name), _core_name(b.entity_name)).ratio()
    return round(0.4 * full_score + 0.6 * core_score, 4)


def geographic_proximity(a: CanonicalRecord, b: CanonicalRecord) -> float | None:
    """None when either record lacks coordinates - this signal is optional."""
    if a.latitude is None or a.longitude is None or b.latitude is None or b.longitude is None:
        return None
    degree_distance = ((a.latitude - b.latitude) ** 2 + (a.longitude - b.longitude) ** 2) ** 0.5
    return max(0.0, 1.0 - degree_distance / 0.05)
