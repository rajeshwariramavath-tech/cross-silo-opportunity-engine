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

OPPORTUNITY_MIN_VALUE_THRESHOLD: float = 5_000_000.0
LOAN_MATURITY_URGENCY_MONTHS: int = 24
STRONG_RELATIONSHIP_CONFIDENCE: float = 0.95

# Composite ranking weight per fired rule - urgency (a past-due loan) outweighs a merely
# large or well-matched deal, so the most time-sensitive opportunities surface first.
OPPORTUNITY_RULE_WEIGHTS: dict[str, int] = {
    "loan_past_due": 3,
    "loan_maturing_soon": 2,
    "high_value_deal": 2,
    "strong_relationship_match": 1,
}
