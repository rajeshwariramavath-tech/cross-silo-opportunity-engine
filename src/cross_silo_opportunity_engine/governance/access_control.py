"""Scopes an opportunity record's fields down to what the requesting role is permitted to see."""

from __future__ import annotations

from typing import Any

from .lineage import trace_field
from .permissions import ROLE_FIELD_PERMISSIONS
from .roles import Role

# Metadata used to build lineage, not business content in its own right - never returned
# as a field, only ever consumed by trace_field() to tag the fields that ARE returned.
_LINEAGE_METADATA_KEYS = {"sales_source_system", "sales_source_id", "debt_source_system", "debt_source_id"}


def scope_result(opportunity: dict[str, Any], requesting_role: Role) -> dict[str, Any]:
    """Renders the same opportunity differently depending on who's asking.

    Every returned field is wrapped with the source_system/source_id it traces back to, so
    scoping never severs lineage - a role that can't see a field never gets it at all, but
    any field it does get always carries proof of where that value came from.
    """
    allowed_fields = ROLE_FIELD_PERMISSIONS.get(requesting_role, set())
    allow_all = "*" in allowed_fields

    scoped: dict[str, Any] = {}
    for field, value in opportunity.items():
        if field in _LINEAGE_METADATA_KEYS:
            continue
        if not allow_all and field not in allowed_fields:
            continue
        scoped[field] = {"value": value, "lineage": trace_field(opportunity, field)}
    return scoped
