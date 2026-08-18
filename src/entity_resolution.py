"""Stage 2 — entity resolution, runnable end to end.

Reads data/processed/canonical_records.csv (Stage 1's output), scores every cross-source
candidate pair on independent signals (address similarity, name similarity, optional
geographic proximity), combines them into one weighted confidence score, and routes each
pair to one of three outcomes: auto-match, review queue, or auto-reject.

Writes every scored pair - not just the auto-matches - to data/processed/entity_matches.csv,
so the ambiguous review-queue and confidently-rejected cases stay visible rather than hidden.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from cross_silo_opportunity_engine.entity_resolution.candidates import generate_candidate_pairs
from cross_silo_opportunity_engine.entity_resolution.outcomes import classify
from cross_silo_opportunity_engine.entity_resolution.scoring import compute_confidence
from cross_silo_opportunity_engine.entity_resolution.signals import (
    address_similarity,
    geographic_proximity,
    name_similarity,
)
from cross_silo_opportunity_engine.ingestion.canonical_schema import CanonicalRecord

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
CANONICAL_RECORDS_PATH = PROCESSED_DIR / "canonical_records.csv"
ENTITY_MATCHES_PATH = PROCESSED_DIR / "entity_matches.csv"

MATCH_FIELDNAMES = [
    "source_system_a", "source_id_a", "entity_name_a",
    "source_system_b", "source_id_b", "entity_name_b",
    "address_similarity", "name_similarity", "geographic_proximity",
    "confidence", "outcome",
]


def load_canonical_records(csv_path: Path) -> list[CanonicalRecord]:
    records = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            records.append(
                CanonicalRecord(
                    source_system=row["source_system"],
                    source_record_id=row["source_record_id"],
                    entity_type=row["entity_type"],
                    entity_name=row["entity_name"],
                    address_line1=row["address_line1"] or None,
                    address_line2=row["address_line2"] or None,
                    city=row["city"] or None,
                    state=row["state"] or None,
                    postal_code=row["postal_code"] or None,
                    latitude=float(row["latitude"]) if row["latitude"] else None,
                    longitude=float(row["longitude"]) if row["longitude"] else None,
                )
            )
    return records


def score_pair(record_a: CanonicalRecord, record_b: CanonicalRecord) -> dict[str, Any]:
    signal_scores = {
        "address_similarity": address_similarity(record_a, record_b),
        "name_similarity": name_similarity(record_a, record_b),
        "geographic_proximity": geographic_proximity(record_a, record_b),
    }
    confidence = compute_confidence(signal_scores)
    outcome = classify(confidence)
    return {
        "source_system_a": record_a.source_system,
        "source_id_a": record_a.source_record_id,
        "entity_name_a": record_a.entity_name,
        "source_system_b": record_b.source_system,
        "source_id_b": record_b.source_record_id,
        "entity_name_b": record_b.entity_name,
        "address_similarity": signal_scores["address_similarity"],
        "name_similarity": signal_scores["name_similarity"],
        "geographic_proximity": signal_scores["geographic_proximity"],
        "confidence": confidence,
        "outcome": outcome.value,
    }


def run_entity_resolution(records: list[CanonicalRecord]) -> list[dict[str, Any]]:
    matches = [score_pair(record_a, record_b) for record_a, record_b in generate_candidate_pairs(records)]
    matches.sort(key=lambda row: row["confidence"], reverse=True)
    return matches


def write_matches(matches: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MATCH_FIELDNAMES)
        writer.writeheader()
        writer.writerows(matches)


def main() -> None:
    records = load_canonical_records(CANONICAL_RECORDS_PATH)
    matches = run_entity_resolution(records)
    write_matches(matches, ENTITY_MATCHES_PATH)

    counts: dict[str, int] = {}
    for row in matches:
        counts[row["outcome"]] = counts.get(row["outcome"], 0) + 1
    print(f"scored pairs: {len(matches)}, by outcome: {counts}")


if __name__ == "__main__":
    main()
