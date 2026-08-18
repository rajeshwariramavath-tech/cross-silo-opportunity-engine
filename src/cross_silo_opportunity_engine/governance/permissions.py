"""Role-to-field-permissions mapping: defined once, applied consistently at every request."""

from __future__ import annotations

from .roles import Role

# "*" means every field is visible; an empty set means only the minimal flag is.
ROLE_FIELD_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"*"},
    Role.BROKER: set(),
    Role.FINANCING: set(),
    Role.VALUATION: set(),
    Role.PROPERTY_MANAGEMENT: set(),
}
