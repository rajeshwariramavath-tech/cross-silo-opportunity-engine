# AI prompts log

Chronological record of the prompts used to build this project with Claude Code, and what
each one produced. Kept for transparency into the AI-assisted development process; prompts
are lightly trimmed for readability, not rewritten.

## 1. Project skeleton

> Set up a Python project skeleton for cross silo opportunity engine using docs/architecture.png
> and docs/architecture.md and read docs/architecture.md first so the folder and file structure
> you create matches the four-stage design described there (ingestion & normalization, entity
> resolution, opportunity detection, governance & access control). do not overwrite anything in
> docs/

Produced the src-layout package (`src/cross_silo_opportunity_engine/`) with one subpackage per
architecture stage, `pyproject.toml`, the `tests/` scaffold, and a README structure section.

## 2. Synthetic source data

> generate two synthetic CSV datasets in data/raw/: sales_records.csv and debt_records.csv
> about 30 rows each that use no shared key, also make them messy and realistic deliberately

Produced `data/raw/sales_records.csv` and `data/raw/debt_records.csv` (30 rows each): 12
entities deliberately overlapping across both files under different name/address spellings, no
shared key between the two ID schemes, mixed date/currency formats, missing fields, and one
duplicate loan entry.

## 3. Stage 1 - ingestion & normalization

> Implement src/ingestion.py per docs/architecture.md Stage 1, read both CSVs, map to one
> canonical schema, Normalize addresses and names and flag invalid rows to
> data/processed/ingestion_rejects.csv instead of dropping them and preserve source_system/
> source_id for lineage, Output data/processed/canonical_records.csv.

Produced `src/ingestion.py` (`SalesCSVAdapter`, `DebtCSVAdapter`) and filled in the package's
address/name normalization. Run against the real data: 54 valid canonical records, 6 flagged
rejects (missing price/amount, missing date, missing address).

## 4. Stage 2 - entity resolution

> Implement src/entity_resolution.py per docs/architecture.md Stage 2 for every canonical pair
> and output matches to data/processed/entity_matches.csv

Produced `src/entity_resolution.py` and filled in the package's address/name/geo similarity
signals, weighted confidence scoring, and three-outcome classification. Run against the real
data: 729 candidate pairs scored - 12 auto-match, 49 review-queue, 668 auto-reject, matching
the 12 entities deliberately planted as shared across both sources.

## 5. Stage 3 - opportunity detection

> Implement src/opportunity_detection.py per docs/architecture.md Stage 3, Add an optional
> generate_rationale() using the Anthropic API - one grounded sentence per opportunity, not
> load bearing for ranking and output it to data/processed/opportunities.csv

Produced `src/opportunity_detection.py`: four deterministic rules (high-value deal, past-due
loan, maturing-soon loan, strong relationship match), composite ranking, and an opt-in
`--rationale` flag calling `generate_rationale()` (Claude Opus 5) that degrades to `None` on
any failure and never affects ranking or qualification. Run against the real data: 12 resolved
matches -> 10 qualifying opportunities.

## 6. Stage 4 - governance & access control

> Implement src/governance.py per docs/architecture.md Stage 4, opportunities + a requesting
> role, return a filtered view via a role -> field-permissions config dict and every returned
> field keeps source_system/source_id for lineage

Produced `src/governance.py` and filled in `ROLE_FIELD_PERMISSIONS` (admin / broker / financing
/ valuation / property_management) and per-field lineage tracing back to the sales and/or debt
source record a field came from.

## 7. Test suite

> write pytests, um, for ingestion, entity resolution, opportunity detection, governance layers

Produced 16 test files (82 tests) covering all four stages - both the generic package modules
and the concrete pipeline scripts - plus a fix for a `datetime.utcnow()` deprecation warning
the test run surfaced.

## 8. Wire up governance + pipeline orchestration

> Governance and pipeline are still stubs, let's finish them. For scope_result(), use the
> ROLE_FIELD_PERMISSIONS and Role enum that already exist, don't build a new permissions
> structure. Keep source_system and source_record_id on every result no matter who's asking,
> only the business fields should get filtered by role. For run_pipeline(), just wire together
> what's already there, call into the ingestion, entityresolution, and opportunity detection
> functions instead of rewriting that logic here. Add a CLI so I can run it like
> python -m cross_silo_opportunity_engine.pipeline --role debt_senior and see the final list.
> Also add prompts/ai_prompts_log.md

Simplified `scope_result()` to a flat dict where any lineage field (`source_system`,
`source_record_id`, or the opportunity schema's `sales_`/`debt_`-prefixed equivalents) always
passes through regardless of role, and only business fields are filtered through the existing
`ROLE_FIELD_PERMISSIONS`. Implemented `run_pipeline()` in
`cross_silo_opportunity_engine/pipeline.py` by sequencing the existing stage scripts' own
functions (no reimplemented logic), with a `python -m cross_silo_opportunity_engine.pipeline
--role <role>` CLI. Note: `debt_senior` isn't one of the defined roles (`admin`, `broker`,
`financing`, `valuation`, `property_management`) - per this same instruction not to build a new
permissions structure, it wasn't added; `--role financing` is the closest existing fit. Added
this log file.
