# cross-silo-opportunity-engine

Connects data across siloed commercial real estate lines of business so cross-business
opportunities surface automatically, without giving anyone unrestricted access to sensitive
data they shouldn't see. See [docs/architecture.md](docs/architecture.md) for the full design.

All four stages run end to end through `pipeline.py`: ingestion & normalization, entity
resolution, opportunity detection, and governance & access control.

## Structure

```
data/raw/                     # Synthetic sales_records.csv / debt_records.csv - two source
                               # systems with no shared key, deliberately messy
data/processed/                # Pipeline output: canonical_records.csv, ingestion_rejects.csv,
                               # entity_matches.csv, opportunities.csv
src/
├── ingestion.py               # Stage 1 entry point - CSV adapters, canonical output
├── entity_resolution.py       # Stage 2 entry point - candidate scoring, entity_matches.csv
├── opportunity_detection.py   # Stage 3 entry point - rules, ranking, opportunities.csv
├── governance.py              # Stage 4 entry point - role-scoped CLI view
└── cross_silo_opportunity_engine/
    ├── ingestion/              # Canonical schema, normalization, adapter interface
    ├── entity_resolution/      # Signals, scoring, three-outcome classification
    ├── opportunity_detection/  # Rules, ranking, optional LLM rationale
    ├── governance/             # Roles, field permissions, access control
    ├── pipeline.py             # Wires all four stages together, with a CLI
    └── config.py               # Shared thresholds and weights
tests/                          # Tests for all four stages, package and entry points alike
prompts/ai_prompts_log.md       # Log of the prompts used to build this project
```

## Setup

```
pip install -e ".[dev]"        # core + test dependencies
pip install -e ".[dev,llm]"    # add the Anthropic SDK for opportunity_detection's --rationale
```

## Run the full pipeline

```
python -m cross_silo_opportunity_engine.pipeline --role <role>
```

`<role>` is one of `admin`, `broker`, `financing`, `valuation`, `property_management`. Prints
the final, role-scoped opportunity list as JSON and leaves each stage's intermediate CSV in
`data/processed/`.

## Run tests

```
pytest
```

Tests cover all four stages - the generic package modules and the concrete entry-point
scripts alike.

## What I built

Real output from actually running this end to end, captured verbatim.

### Tests

```
$ pytest -v
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\rajes\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\rajes\cross-silo-opportunity-engine
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.14.2
collecting ... collected 84 items

tests/entity_resolution/test_candidates.py::test_generate_candidate_pairs_only_crosses_sources PASSED [  1%]
tests/entity_resolution/test_candidates.py::test_generate_candidate_pairs_excludes_same_source_pairs PASSED [  2%]
tests/entity_resolution/test_candidates.py::test_generate_candidate_pairs_empty_input PASSED [  3%]
tests/entity_resolution/test_entity_resolution_pipeline.py::test_score_pair_matching_entity_auto_matches PASSED [  4%]
tests/entity_resolution/test_entity_resolution_pipeline.py::test_score_pair_unrelated_entities_auto_rejects PASSED [  5%]
tests/entity_resolution/test_entity_resolution_pipeline.py::test_run_entity_resolution_sorts_by_confidence_descending PASSED [  7%]
tests/entity_resolution/test_entity_resolution_pipeline.py::test_load_canonical_records_round_trips_csv PASSED [  8%]
tests/entity_resolution/test_outcomes.py::test_classify_at_or_above_auto_match_threshold PASSED [  9%]
tests/entity_resolution/test_outcomes.py::test_classify_just_below_auto_match_threshold_is_review PASSED [ 10%]
tests/entity_resolution/test_outcomes.py::test_classify_at_or_below_auto_reject_threshold PASSED [ 11%]
tests/entity_resolution/test_outcomes.py::test_classify_just_above_auto_reject_threshold_is_review PASSED [ 13%]
tests/entity_resolution/test_outcomes.py::test_classify_mid_range_is_review PASSED [ 14%]
tests/entity_resolution/test_scoring.py::test_compute_confidence_with_all_signals_present PASSED [ 15%]
tests/entity_resolution/test_scoring.py::test_compute_confidence_renormalizes_when_a_signal_is_missing PASSED [ 16%]
tests/entity_resolution/test_scoring.py::test_compute_confidence_all_signals_missing_is_zero PASSED [ 17%]
tests/entity_resolution/test_scoring.py::test_compute_confidence_ignores_unknown_signal_keys PASSED [ 19%]
tests/entity_resolution/test_signals.py::test_address_similarity_identical_is_one PASSED [ 20%]
tests/entity_resolution/test_signals.py::test_address_similarity_missing_line1_is_zero PASSED [ 21%]
tests/entity_resolution/test_signals.py::test_address_similarity_different_address_is_low PASSED [ 22%]
tests/entity_resolution/test_signals.py::test_name_similarity_legal_suffix_difference_scores_high PASSED [ 23%]
tests/entity_resolution/test_signals.py::test_name_similarity_different_names_scores_low PASSED [ 25%]
tests/entity_resolution/test_signals.py::test_name_similarity_missing_name_is_zero PASSED [ 26%]
tests/entity_resolution/test_signals.py::test_geographic_proximity_none_when_coordinates_missing PASSED [ 27%]
tests/entity_resolution/test_signals.py::test_geographic_proximity_same_point_is_high PASSED [ 28%]
tests/entity_resolution/test_signals.py::test_geographic_proximity_far_apart_clamps_to_zero PASSED [ 29%]
tests/governance/test_access_control.py::test_admin_sees_every_business_field_plus_lineage PASSED [ 30%]
tests/governance/test_access_control.py::test_property_management_sees_the_minimal_flag_plus_lineage PASSED [ 32%]
tests/governance/test_access_control.py::test_lineage_fields_survive_every_role_even_when_no_business_fields_do PASSED [ 33%]
tests/governance/test_governance_pipeline.py::test_get_opportunities_for_role_applies_scoping_per_role PASSED [ 34%]
tests/governance/test_governance_pipeline.py::test_load_opportunities_coerces_types PASSED [ 35%]
tests/governance/test_governance_pipeline.py::test_load_opportunities_handles_no_fired_rules PASSED [ 36%]
tests/governance/test_lineage.py::test_sales_field_traces_to_sales_record_only PASSED [ 38%]
tests/governance/test_lineage.py::test_debt_field_traces_to_debt_record_only PASSED [ 39%]
tests/governance/test_lineage.py::test_derived_field_traces_to_both_records PASSED [ 40%]
tests/governance/test_lineage.py::test_unknown_field_traces_to_nothing PASSED [ 41%]
tests/governance/test_permissions.py::test_admin_sees_everything PASSED  [ 42%]
tests/governance/test_permissions.py::test_every_non_admin_role_is_covered_and_bounded PASSED [ 44%]
tests/governance/test_permissions.py::test_broker_and_financing_do_not_see_each_others_lob_fields PASSED [ 45%]
tests/governance/test_permissions.py::test_property_management_gets_minimal_flag_only PASSED [ 46%]
tests/ingestion/test_ingestion_pipeline.py::test_sales_adapter_to_canonical_normalizes_and_preserves_lineage PASSED [ 47%]
tests/ingestion/test_ingestion_pipeline.py::test_debt_adapter_to_canonical_splits_combined_address PASSED [ 48%]
tests/ingestion/test_ingestion_pipeline.py::test_missing_raw_fields_reports_blank_required_fields PASSED [ 50%]
tests/ingestion/test_ingestion_pipeline.py::test_run_ingestion_splits_valid_and_rejected_rows PASSED [ 51%]
tests/ingestion/test_normalization.py::test_normalize_address_extracts_suite PASSED [ 52%]
tests/ingestion/test_normalization.py::test_normalize_address_extracts_inline_floor_abbreviation PASSED [ 53%]
tests/ingestion/test_normalization.py::test_normalize_address_extracts_ordinal_floor PASSED [ 54%]
tests/ingestion/test_normalization.py::test_normalize_address_no_unit PASSED [ 55%]
tests/ingestion/test_normalization.py::test_normalize_address_expands_suffix_abbreviation PASSED [ 57%]
tests/ingestion/test_normalization.py::test_normalize_address_does_not_false_positive_on_ste_inside_a_word PASSED [ 58%]
tests/ingestion/test_normalization.py::test_normalize_address_empty_input PASSED [ 59%]
tests/ingestion/test_normalization.py::test_split_combined_address_matches_separate_fields_normalization PASSED [ 60%]
tests/ingestion/test_normalization.py::test_split_combined_address_full_state_name PASSED [ 61%]
tests/ingestion/test_normalization.py::test_split_combined_address_missing_zip_returns_all_none PASSED [ 63%]
tests/ingestion/test_normalization.py::test_split_combined_address_empty_input PASSED [ 64%]
tests/ingestion/test_normalization.py::test_normalize_entity_name_strips_legal_suffix_variants PASSED [ 65%]
tests/ingestion/test_normalization.py::test_normalize_entity_name_collapses_whitespace_and_case PASSED [ 66%]
tests/ingestion/test_normalization.py::test_normalize_entity_name_strips_trailing_punctuation PASSED [ 67%]
tests/ingestion/test_normalization.py::test_normalize_entity_name_empty_input PASSED [ 69%]
tests/ingestion/test_normalization.py::test_normalize_state_two_letter_uppercases PASSED [ 70%]
tests/ingestion/test_normalization.py::test_normalize_state_full_name_lookup PASSED [ 71%]
tests/ingestion/test_normalization.py::test_normalize_state_unknown_title_cases PASSED [ 72%]
tests/ingestion/test_normalization.py::test_normalize_state_empty_is_none PASSED [ 73%]
tests/ingestion/test_validation.py::test_validate_record_all_required_fields_present PASSED [ 75%]
tests/ingestion/test_validation.py::test_validate_record_missing_entity_name PASSED [ 76%]
tests/ingestion/test_validation.py::test_validate_record_missing_multiple_fields PASSED [ 77%]
tests/opportunity_detection/test_explanation.py::test_generate_rationale_returns_none_when_anthropic_not_installed PASSED [ 78%]
tests/opportunity_detection/test_explanation.py::test_generate_rationale_returns_none_on_api_failure PASSED [ 79%]
tests/opportunity_detection/test_explanation.py::test_generate_rationale_returns_grounded_text_on_success PASSED [ 80%]
tests/opportunity_detection/test_opportunity_detection_pipeline.py::test_parse_currency_handles_dollar_sign_and_commas PASSED [ 82%]
tests/opportunity_detection/test_opportunity_detection_pipeline.py::test_parse_currency_handles_plain_number_string PASSED [ 83%]
tests/opportunity_detection/test_opportunity_detection_pipeline.py::test_parse_currency_empty_or_invalid_is_none PASSED [ 84%]
tests/opportunity_detection/test_opportunity_detection_pipeline.py::test_parse_date_valid_iso PASSED [ 85%]
tests/opportunity_detection/test_opportunity_detection_pipeline.py::test_parse_date_invalid_format_is_none PASSED [ 86%]
tests/opportunity_detection/test_opportunity_detection_pipeline.py::test_build_opportunity_merges_sales_and_debt_sides PASSED [ 88%]
tests/opportunity_detection/test_opportunity_detection_pipeline.py::test_build_opportunity_missing_lookup_returns_none PASSED [ 89%]
tests/opportunity_detection/test_opportunity_detection_pipeline.py::test_past_due_loan_fires_urgency_rule_even_under_value_threshold PASSED [ 90%]
tests/opportunity_detection/test_opportunity_detection_pipeline.py::test_no_rules_fire_excludes_the_match PASSED [ 91%]
tests/opportunity_detection/test_ranking.py::test_rank_opportunities_sorts_descending_by_composite_score PASSED [ 92%]
tests/opportunity_detection/test_ranking.py::test_rank_opportunities_empty_list PASSED [ 94%]
tests/opportunity_detection/test_rules.py::test_evaluate_rules_returns_only_fired_rule_names_in_order PASSED [ 95%]
tests/opportunity_detection/test_rules.py::test_evaluate_rules_empty_rule_list PASSED [ 96%]
tests/test_pipeline.py::test_run_pipeline_property_management_sees_minimal_flag_with_lineage PASSED [ 97%]
tests/test_pipeline.py::test_run_pipeline_admin_sees_business_fields_the_others_dont PASSED [ 98%]
tests/test_pipeline.py::test_run_pipeline_ranking_is_preserved_through_governance PASSED [100%]

============================= 84 passed in 3.07s ==============================
```

### Pipeline — `--role financing`

Financing sees loan-side detail (amount, dates, lender, past-due notes) but no `sale_price` or
`broker_name`. Silverline Capital tops the list twice - once per debt-side record, since the
source data has a duplicate loan entry (`DBT-2024-003` and `DBT-2024-030`) and each is a
distinct, individually-traceable resolved match.

```
$ python -m cross_silo_opportunity_engine.pipeline --role financing
[
  {
    "entity_name": "Silverline Capital",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1003",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-003",
    "property_type": "Office",
    "loan_amount": "4900000",
    "orig_date": "03/01/2024",
    "maturity_date": "2031-03-01",
    "lender_name": "Republic Trust Bank",
    "loan_type": "Term Loan",
    "notes": "past due 30 days",
    "entity_resolution_confidence": 0.9822,
    "fired_rules": [
      "high_value_deal",
      "loan_past_due",
      "strong_relationship_match"
    ],
    "composite_score": 6
  },
  {
    "entity_name": "Silverline Capital",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1003",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-030",
    "property_type": "Office",
    "loan_amount": "4900000",
    "orig_date": "03/01/2024",
    "maturity_date": "2031-03-01",
    "lender_name": "Republic Trust Bank",
    "loan_type": "Term Loan",
    "notes": "past due 30 days",
    "entity_resolution_confidence": 0.9822,
    "fired_rules": [
      "high_value_deal",
      "loan_past_due",
      "strong_relationship_match"
    ],
    "composite_score": 6
  },
  {
    "entity_name": "Bluepeak Realty Trust",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1006",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-006",
    "property_type": "Retail",
    "loan_amount": "5500000",
    "orig_date": "01/05/2024",
    "maturity_date": "2028-01-05",
    "lender_name": "Lakefront Bank",
    "loan_type": "Refinance",
    "notes": "",
    "entity_resolution_confidence": 1.0,
    "fired_rules": [
      "high_value_deal",
      "loan_maturing_soon",
      "strong_relationship_match"
    ],
    "composite_score": 5
  },
  {
    "entity_name": "Pinnacle Office Trust",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1011",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-011",
    "property_type": "Office",
    "loan_amount": "6700000",
    "orig_date": "06/02/2024",
    "maturity_date": "2031-06-02",
    "lender_name": "Pacific Northwest Trust",
    "loan_type": "Term Loan",
    "notes": "",
    "entity_resolution_confidence": 1.0,
    "fired_rules": [
      "high_value_deal",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Crestpoint Industrial Partners",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1005",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-005",
    "property_type": "Industrial",
    "loan_amount": "3600000",
    "orig_date": "2024-02-28",
    "maturity_date": "2030-02-28",
    "lender_name": "Delta Commercial Credit",
    "loan_type": "Term Loan",
    "notes": "",
    "entity_resolution_confidence": 0.9889,
    "fired_rules": [
      "high_value_deal",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Redwood Multifamily Group",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1012",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-012",
    "property_type": "Multifamily",
    "loan_amount": "8100000",
    "orig_date": "2024-02-08",
    "maturity_date": "2030-02-08",
    "lender_name": "Golden State Credit Union",
    "loan_type": "Refinance",
    "notes": "",
    "entity_resolution_confidence": 0.9868,
    "fired_rules": [
      "high_value_deal",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Oakwood Retail Partners",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1002",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-002",
    "property_type": "Retail",
    "loan_amount": "1200000",
    "orig_date": "2024-02-15",
    "maturity_date": "2027-02-15",
    "lender_name": "Highline Lending",
    "loan_type": "Bridge Loan",
    "notes": "",
    "entity_resolution_confidence": 0.9858,
    "fired_rules": [
      "loan_maturing_soon",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Delta Ridge Ventures",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1009",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-009",
    "property_type": "Retail",
    "loan_amount": "1450000",
    "orig_date": "05/09/2024",
    "maturity_date": "2027-05-09",
    "lender_name": "Crescent City Lending",
    "loan_type": "Bridge Loan",
    "notes": "",
    "entity_resolution_confidence": 0.9838,
    "fired_rules": [
      "loan_maturing_soon",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Northgate Logistics",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1008",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-008",
    "property_type": "Industrial",
    "loan_amount": "3950000",
    "orig_date": "2024-03-11",
    "maturity_date": "2029-03-11",
    "lender_name": "Volunteer State Bank",
    "loan_type": "Construction Loan",
    "notes": "",
    "entity_resolution_confidence": 0.9831,
    "fired_rules": [
      "high_value_deal",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Cornerstone Retail Fund",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1010",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-010",
    "property_type": "Retail",
    "loan_amount": "2900000",
    "orig_date": "2024-01-22",
    "maturity_date": "2029-01-22",
    "lender_name": "Gulf Coast Bank",
    "loan_type": "Term Loan",
    "notes": "",
    "entity_resolution_confidence": 1.0,
    "fired_rules": [
      "strong_relationship_match"
    ],
    "composite_score": 1
  }
]
```

### Pipeline — `--role broker`

Same 10 opportunities, same ranking - but broker sees `sale_price`/`close_date`/`broker_name`
instead of loan detail. Neither role sees the other's line-of-business fields; both keep full
lineage back to the source records on every row.

```
$ python -m cross_silo_opportunity_engine.pipeline --role broker
[
  {
    "entity_name": "Silverline Capital",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1003",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-003",
    "sale_price": "7600000",
    "close_date": "March 22, 2024",
    "broker_name": "",
    "property_type": "Office",
    "entity_resolution_confidence": 0.9822,
    "fired_rules": [
      "high_value_deal",
      "loan_past_due",
      "strong_relationship_match"
    ],
    "composite_score": 6
  },
  {
    "entity_name": "Silverline Capital",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1003",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-030",
    "sale_price": "7600000",
    "close_date": "March 22, 2024",
    "broker_name": "",
    "property_type": "Office",
    "entity_resolution_confidence": 0.9822,
    "fired_rules": [
      "high_value_deal",
      "loan_past_due",
      "strong_relationship_match"
    ],
    "composite_score": 6
  },
  {
    "entity_name": "Bluepeak Realty Trust",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1006",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-006",
    "sale_price": "9100000",
    "close_date": "2024-01-19",
    "broker_name": "Derek Wu",
    "property_type": "Retail",
    "entity_resolution_confidence": 1.0,
    "fired_rules": [
      "high_value_deal",
      "loan_maturing_soon",
      "strong_relationship_match"
    ],
    "composite_score": 5
  },
  {
    "entity_name": "Pinnacle Office Trust",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1011",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-011",
    "sale_price": "8900000",
    "close_date": "06/11/2024",
    "broker_name": "Maria Chen",
    "property_type": "Office",
    "entity_resolution_confidence": 1.0,
    "fired_rules": [
      "high_value_deal",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Crestpoint Industrial Partners",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1005",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-005",
    "sale_price": "5300000",
    "close_date": "04/02/2024",
    "broker_name": "Priya Nair",
    "property_type": "Industrial",
    "entity_resolution_confidence": 0.9889,
    "fired_rules": [
      "high_value_deal",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Redwood Multifamily Group",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1012",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-012",
    "sale_price": "11200000",
    "close_date": "2024-02-27",
    "broker_name": "Derek Wu",
    "property_type": "Multifamily",
    "entity_resolution_confidence": 0.9868,
    "fired_rules": [
      "high_value_deal",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Oakwood Retail Partners",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1002",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-002",
    "sale_price": "$1,850,000",
    "close_date": "2024-02-01",
    "broker_name": "Maria Chen",
    "property_type": "Retail",
    "entity_resolution_confidence": 0.9858,
    "fired_rules": [
      "loan_maturing_soon",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Delta Ridge Ventures",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1009",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-009",
    "sale_price": "2100000",
    "close_date": "05/17/2024",
    "broker_name": "",
    "property_type": "Retail",
    "entity_resolution_confidence": 0.9838,
    "fired_rules": [
      "loan_maturing_soon",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Northgate Logistics",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1008",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-008",
    "sale_price": "6250000",
    "close_date": "2024-05-03",
    "broker_name": "Priya Nair",
    "property_type": "Industrial",
    "entity_resolution_confidence": 0.9831,
    "fired_rules": [
      "high_value_deal",
      "strong_relationship_match"
    ],
    "composite_score": 3
  },
  {
    "entity_name": "Cornerstone Retail Fund",
    "sales_source_system": "sales_records",
    "sales_source_id": "SR-1010",
    "debt_source_system": "debt_records",
    "debt_source_id": "DBT-2024-010",
    "sale_price": "4750000",
    "close_date": "2024-03-29",
    "broker_name": "J. Alvarez",
    "property_type": "Retail",
    "entity_resolution_confidence": 1.0,
    "fired_rules": [
      "strong_relationship_match"
    ],
    "composite_score": 1
  }
]
```

## How this was built

See [prompts/ai_prompts_log.md](prompts/ai_prompts_log.md) for the prompt-by-prompt history.
