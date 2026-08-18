"""Roles that opportunity results can be scoped to. Extend as new lines of business are added."""

from __future__ import annotations

from enum import Enum


class Role(Enum):
    ADMIN = "admin"
    BROKER = "broker"
    FINANCING = "financing"
    VALUATION = "valuation"
    PROPERTY_MANAGEMENT = "property_management"
