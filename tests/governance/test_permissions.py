from cross_silo_opportunity_engine.governance.permissions import ROLE_FIELD_PERMISSIONS
from cross_silo_opportunity_engine.governance.roles import Role


def test_admin_sees_everything():
    assert ROLE_FIELD_PERMISSIONS[Role.ADMIN] == {"*"}


def test_every_non_admin_role_is_covered_and_bounded():
    for role in Role:
        if role is Role.ADMIN:
            continue
        fields = ROLE_FIELD_PERMISSIONS[role]
        assert "*" not in fields
        assert fields, f"{role} should see at least the shared opportunity signal"


def test_broker_and_financing_do_not_see_each_others_lob_fields():
    broker_fields = ROLE_FIELD_PERMISSIONS[Role.BROKER]
    financing_fields = ROLE_FIELD_PERMISSIONS[Role.FINANCING]

    assert "loan_amount" not in broker_fields
    assert "notes" not in broker_fields
    assert "sale_price" not in financing_fields
    assert "broker_name" not in financing_fields
    assert {"entity_name", "property_type"} <= broker_fields
    assert {"entity_name", "property_type"} <= financing_fields


def test_property_management_gets_minimal_flag_only():
    assert ROLE_FIELD_PERMISSIONS[Role.PROPERTY_MANAGEMENT] == {"entity_name", "property_type"}
