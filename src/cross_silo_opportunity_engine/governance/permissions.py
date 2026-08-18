"""Role-to-field-permissions mapping: defined once, applied consistently at every request."""

from __future__ import annotations

from .roles import Role

# "*" means every field is visible. Each role otherwise gets the shared opportunity signal
# (entity_name, property_type, and the rule outcome) plus only its own line of business's
# financial detail - a broker doesn't need the borrower's delinquency notes to act on a
# lead, and financing doesn't need the sale broker's name. Property management sits outside
# both LOBs and gets the architecture doc's "minimal flag": just enough to know an
# opportunity exists, with every dollar figure and counterparty name withheld.
ROLE_FIELD_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"*"},
    Role.BROKER: {
        "entity_name", "property_type",
        "sale_price", "close_date", "broker_name",
        "entity_resolution_confidence", "fired_rules", "composite_score", "rationale",
    },
    Role.FINANCING: {
        "entity_name", "property_type",
        "loan_amount", "orig_date", "maturity_date", "lender_name", "loan_type", "notes",
        "entity_resolution_confidence", "fired_rules", "composite_score", "rationale",
    },
    Role.VALUATION: {
        "entity_name", "property_type",
        "fired_rules", "composite_score",
    },
    Role.PROPERTY_MANAGEMENT: {
        "entity_name", "property_type",
    },
}
