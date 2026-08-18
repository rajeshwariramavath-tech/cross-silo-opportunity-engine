"""Adapter interface: reads one source system's native format, emits CanonicalRecords."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Iterator

from ..canonical_schema import CanonicalRecord


class BaseSourceAdapter(ABC):
    source_system: str

    @abstractmethod
    def read(self) -> Iterable[dict[str, Any]]:
        """Yields raw records in the source system's own native format."""
        raise NotImplementedError

    @abstractmethod
    def to_canonical(self, raw_record: dict[str, Any]) -> CanonicalRecord:
        """Converts one raw record into the canonical shape, preserving lineage metadata."""
        raise NotImplementedError

    def run(self) -> Iterator[CanonicalRecord]:
        for raw_record in self.read():
            yield self.to_canonical(raw_record)
