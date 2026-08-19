"""Times Stage 2 (entity resolution) with zip-code blocking vs. without it, on the real
canonical records in data/processed/canonical_records.csv.

"Without blocking" reimplements the pre-blocking full cross-source pairing inline (every
Sales record against every Debt record) purely for this comparison - it's not how the
pipeline actually runs any more; cross_silo_opportunity_engine.entity_resolution.candidates
now only ever does the blocked version. Run: python scripts/benchmark_entity_resolution.py
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable, Iterator

from cross_silo_opportunity_engine.entity_resolution.candidates import generate_candidate_pairs
from cross_silo_opportunity_engine.entity_resolution.outcomes import classify
from cross_silo_opportunity_engine.entity_resolution.scoring import compute_confidence
from cross_silo_opportunity_engine.entity_resolution.signals import (
    address_similarity,
    geographic_proximity,
    name_similarity,
)
from cross_silo_opportunity_engine.ingestion.canonical_schema import CanonicalRecord

from entity_resolution import load_canonical_records

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_RECORDS_PATH = REPO_ROOT / "data" / "processed" / "canonical_records.csv"


def generate_candidate_pairs_unblocked(
    records: Iterable[CanonicalRecord],
) -> Iterator[tuple[CanonicalRecord, CanonicalRecord]]:
    """The pre-blocking behavior: every record against every record from a different source
    system, with no zip partitioning. Kept here only for this benchmark's comparison."""
    records = list(records)
    for i, record_a in enumerate(records):
        for record_b in records[i + 1:]:
            if record_a.source_system != record_b.source_system:
                yield record_a, record_b


def score_all(pairs: Iterator[tuple[CanonicalRecord, CanonicalRecord]]) -> int:
    count = 0
    for record_a, record_b in pairs:
        signal_scores = {
            "address_similarity": address_similarity(record_a, record_b),
            "name_similarity": name_similarity(record_a, record_b),
            "geographic_proximity": geographic_proximity(record_a, record_b),
        }
        classify(compute_confidence(signal_scores))
        count += 1
    return count


def timed(label: str, pair_generator, records: list[CanonicalRecord]) -> None:
    start = time.perf_counter()
    pair_count = score_all(pair_generator(records))
    elapsed = time.perf_counter() - start
    per_pair_us = (elapsed / pair_count * 1_000_000) if pair_count else 0.0
    print(f"{label}: {pair_count:,} pairs scored in {elapsed:.3f}s ({per_pair_us:.1f} us/pair)")


def main() -> None:
    records = load_canonical_records(CANONICAL_RECORDS_PATH)
    print(f"canonical records: {len(records)}\n")

    timed("without blocking (every Sales x every Debt record)", generate_candidate_pairs_unblocked, records)
    timed("with zip-code blocking (current implementation)", generate_candidate_pairs, records)


if __name__ == "__main__":
    main()
