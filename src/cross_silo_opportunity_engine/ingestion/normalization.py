"""Address and entity-name normalization applied before records enter entity resolution."""

from __future__ import annotations


def normalize_address(raw_address: str) -> dict[str, str | None]:
    """Normalizes case/abbreviations and splits suite/floor into their own fields."""
    raise NotImplementedError


def normalize_entity_name(raw_name: str) -> str:
    raise NotImplementedError
