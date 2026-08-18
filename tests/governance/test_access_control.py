from cross_silo_opportunity_engine.governance.access_control import scope_result
from cross_silo_opportunity_engine.governance.roles import Role


def _opportunity():
    return {
        "entity_name": "Silverline Capital",
        "property_type": "Office",
        "sale_price": "7600000",
        "loan_amount": "4900000",
        "notes": "past due 30 days",
        "fired_rules": ["high_value_deal", "loan_past_due"],
        "composite_score": 6,
        "sales_source_system": "sales_records",
        "sales_source_id": "SR-1003",
        "debt_source_system": "debt_records",
        "debt_source_id": "DBT-2024-003",
    }


def test_admin_sees_every_business_field_plus_lineage():
    scoped = scope_result(_opportunity(), Role.ADMIN)

    assert scoped == _opportunity()  # "*" passes every field through untouched


def test_property_management_sees_the_minimal_flag_plus_lineage():
    scoped = scope_result(_opportunity(), Role.PROPERTY_MANAGEMENT)

    assert scoped == {
        "entity_name": "Silverline Capital",
        "property_type": "Office",
        "sales_source_system": "sales_records",
        "sales_source_id": "SR-1003",
        "debt_source_system": "debt_records",
        "debt_source_id": "DBT-2024-003",
    }
    assert "sale_price" not in scoped
    assert "loan_amount" not in scoped
    assert "notes" not in scoped


def test_lineage_fields_survive_every_role_even_when_no_business_fields_do():
    class _NoPermissionsRole:
        pass

    # Not a real Role - ROLE_FIELD_PERMISSIONS.get() falls back to an empty set, so no
    # business field is allowed, but lineage must still come through unconditionally.
    scoped = scope_result(_opportunity(), _NoPermissionsRole())

    assert scoped == {
        "sales_source_system": "sales_records",
        "sales_source_id": "SR-1003",
        "debt_source_system": "debt_records",
        "debt_source_id": "DBT-2024-003",
    }
