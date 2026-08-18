"""Scopes an opportunity record's fields down to what the requesting role is permitted to see."""

from __future__ import annotations

from typing import Any

from .permissions import ROLE_FIELD_PERMISSIONS
from .roles import Role

# Any field ending in one of these is a lineage identifier, not business content - it's
# never filtered by role. Matches CanonicalRecord's own "source_system"/"source_record_id"
# as well as the opportunity schema's per-side "sales_source_system"/"debt_source_id" etc.
_LINEAGE_FIELD_SUFFIXES = ("source_system", "source_record_id", "source_id")


def scope_result(opportunity: dict[str, Any], requesting_role: Role) -> dict[str, Any]:
    """Renders the same opportunity differently depending on who's asking.

    Only business fields are filtered by ROLE_FIELD_PERMISSIONS - every source_system/
    source_id (or sales_/debt_-prefixed equivalent) stays on the result no matter the role,
    so a number can always be traced back to the record it came from.
    """
    allowed_fields = ROLE_FIELD_PERMISSIONS.get(requesting_role, set())
    allow_all = "*" in allowed_fields

    return {
        field: value
        for field, value in opportunity.items()
        if field.endswith(_LINEAGE_FIELD_SUFFIXES) or allow_all or field in allowed_fields
    }
