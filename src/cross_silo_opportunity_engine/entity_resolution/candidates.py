"""Candidate pair generation: blocks records before pairwise signal scoring."""

from __future__ import annotations

from typing import Iterable, Iterator

from ..ingestion.canonical_schema import CanonicalRecord


def generate_candidate_pairs(
    records: Iterable[CanonicalRecord],
) -> Iterator[tuple[CanonicalRecord, CanonicalRecord]]:
    """Blocks by postal code (first 5 digits) before pairing across source systems.

    A Sales record is only ever compared against Debt records in the same zip block, not
    every Debt record - this is what keeps pairwise scoring from growing quadratically with
    the dataset. Matching within one source still isn't the problem this stage solves, so
    same-source records within a block are skipped too. Records with no postal code can't be
    blocked and produce no candidate pairs.
    """
    by_zip: dict[str, list[CanonicalRecord]] = {}
    for record in records:
        if not record.postal_code:
            continue
        zip5 = record.postal_code[:5]
        by_zip.setdefault(zip5, []).append(record)

    for block in by_zip.values():
        for i, record_a in enumerate(block):
            for record_b in block[i + 1:]:
                if record_a.source_system != record_b.source_system:
                    yield record_a, record_b
