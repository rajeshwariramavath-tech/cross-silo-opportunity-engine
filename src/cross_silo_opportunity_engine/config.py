"""Single source of truth for thresholds and weights shared across stages."""

REQUIRED_CANONICAL_FIELDS: list[str] = [
    "source_system",
    "source_record_id",
    "entity_type",
    "entity_name",
]

ENTITY_RESOLUTION_SIGNAL_WEIGHTS: dict[str, float] = {
    "address_similarity": 0.5,
    "name_similarity": 0.4,
    "geographic_proximity": 0.1,
}

AUTO_MATCH_THRESHOLD: float = 0.85
AUTO_REJECT_THRESHOLD: float = 0.4

OPPORTUNITY_MIN_VALUE_THRESHOLD: float = 0.0
