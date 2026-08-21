"""End-to-end check that run_pipeline() actually wires the three processing stages and
governance together correctly against the real data/raw CSVs - each part's own tests already
cover its internals."""

from cross_silo_opportunity_engine.governance.roles import Role
from cross_silo_opportunity_engine.pipeline import run_pipeline


def test_run_pipeline_property_management_sees_minimal_flag_with_lineage():
    scoped = run_pipeline(Role.PROPERTY_MANAGEMENT)

    assert scoped  # real data has qualifying opportunities
    for opportunity in scoped:
        assert set(opportunity.keys()) == {
            "entity_name", "property_type",
            "sales_source_system", "sales_source_id", "debt_source_system", "debt_source_id",
        }
        assert opportunity["sales_source_system"] == "sales_records"
        assert opportunity["debt_source_system"] == "debt_records"


def test_run_pipeline_admin_sees_business_fields_the_others_dont():
    scoped = run_pipeline(Role.ADMIN)

    assert scoped
    assert any("sale_price" in opportunity for opportunity in scoped)
    assert any("loan_amount" in opportunity for opportunity in scoped)


def test_run_pipeline_ranking_is_preserved_through_governance():
    admin_view = run_pipeline(Role.ADMIN)
    scores = [opportunity["composite_score"] for opportunity in admin_view]
    assert scores == sorted(scores, reverse=True)
