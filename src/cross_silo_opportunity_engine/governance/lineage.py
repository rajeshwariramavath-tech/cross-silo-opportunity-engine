"""Traces any field in a final opportunity record back to its original source record."""

from __future__ import annotations

from typing import Any

# Which side of the resolved match produced each field in an opportunity record. Fields the
# rules/entity-resolution stages computed from *both* sides (confidence, fired rules, the
# composite score, the optional rationale) trace to both source records, not just one.
_SALES_FIELDS = {"entity_name", "sale_price", "close_date", "broker_name", "property_type"}
_DEBT_FIELDS = {"loan_amount", "orig_date", "maturity_date", "lender_name", "loan_type", "notes"}
_DERIVED_FIELDS = {"entity_resolution_confidence", "fired_rules", "composite_score", "rationale"}


def trace_field(opportunity: dict[str, Any], field_name: str) -> list[dict[str, str]]:
    """Returns the one or two source-record references a field's value came from."""
    sales_ref = {
        "source_system": opportunity["sales_source_system"],
        "source_id": opportunity["sales_source_id"],
    }
    debt_ref = {
        "source_system": opportunity["debt_source_system"],
        "source_id": opportunity["debt_source_id"],
    }

    if field_name in _SALES_FIELDS:
        return [sales_ref]
    if field_name in _DEBT_FIELDS:
        return [debt_ref]
    if field_name in _DERIVED_FIELDS:
        return [sales_ref, debt_ref]
    return []
