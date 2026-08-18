"""Traces any field in a final opportunity record back to its original source record."""

from __future__ import annotations

from typing import Any


def trace_field(opportunity: dict[str, Any], field_name: str) -> dict[str, Any]:
    raise NotImplementedError
