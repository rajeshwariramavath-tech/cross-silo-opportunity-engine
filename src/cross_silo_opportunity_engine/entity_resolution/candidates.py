"""Candidate pair generation: blocks records before pairwise signal scoring."""

from __future__ import annotations

from typing import Iterable, Iterator

from ..ingestion.canonical_schema import CanonicalRecord


def generate_candidate_pairs(
    records: Iterable[CanonicalRecord],
) -> Iterator[tuple[CanonicalRecord, CanonicalRecord]]:
    raise NotImplementedError
