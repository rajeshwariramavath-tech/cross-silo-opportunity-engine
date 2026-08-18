"""Candidate pair generation: blocks records before pairwise signal scoring."""

from __future__ import annotations

from typing import Iterable, Iterator

from ..ingestion.canonical_schema import CanonicalRecord


def generate_candidate_pairs(
    records: Iterable[CanonicalRecord],
) -> Iterator[tuple[CanonicalRecord, CanonicalRecord]]:
    """Pairs records from different source systems.

    Matching within one source isn't the problem this stage solves - records from the same
    source already share that source's own ID scheme. Blocking by "different source system"
    is what keeps this a cross-silo linking step rather than an in-system dedupe step.
    """
    records = list(records)
    for i, record_a in enumerate(records):
        for record_b in records[i + 1:]:
            if record_a.source_system != record_b.source_system:
                yield record_a, record_b
