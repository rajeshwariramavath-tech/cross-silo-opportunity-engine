"""Scopes an opportunity record's fields down to what the requesting role is permitted to see."""

from __future__ import annotations

from typing import Any

from .permissions import ROLE_FIELD_PERMISSIONS
from .roles import Role


def scope_result(opportunity: dict[str, Any], requesting_role: Role) -> dict[str, Any]:
    raise NotImplementedError
