"""Required-field validation for canonical records. Invalid records are flagged, not dropped."""

from __future__ import annotations

from dataclasses import dataclass

from .canonical_schema import CanonicalRecord
from ..config import REQUIRED_CANONICAL_FIELDS


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]


def validate_record(record: CanonicalRecord) -> ValidationResult:
    errors = [
        field_name
        for field_name in REQUIRED_CANONICAL_FIELDS
        if not getattr(record, field_name, None)
    ]
    return ValidationResult(is_valid=not errors, errors=errors)
