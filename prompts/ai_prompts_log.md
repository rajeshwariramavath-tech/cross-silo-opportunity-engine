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

## 9. README with real captured output

> Run pytest -v, and run the pipeline end to end for both financing and broker roles. Take the
> real output from all of that and put it under README.md's "What I built" section, run
> instructions plus the actual output, no placeholder text.

Ran `pytest -v` (84 tests) and `python -m cross_silo_opportunity_engine.pipeline --role
financing` / `--role broker` for real, then pasted the verbatim output - not illustrative,
not trimmed - into a new "What I built" section in `README.md`.

## 10. HTML pipeline report

> Write a script scripts/generate_report.py that reads the existing CSVs in data/processed/
> and generates a single self-contained docs/report.html so it opens directly in a browser or
> renders on GitHub Pages if I turn that on later. Include, top to bottom: the architecture
> diagram... a small summary stats row... the ranked opportunities table, and side by side, the
> same opportunities scoped through governance for the financing role vs the broker role...
> Keep the styling simple and clean... use the same color palette as the architecture diagram
> if easy (muted greens/oranges/purples). Run the script and confirm docs/report.html actually
> renders correctly before i commit.

Produced `scripts/generate_report.py`, which reuses the real `governance.get_opportunities_for_role()`
rather than re-deriving who-sees-what, and samples its palette from the actual
`docs/architecture.png`. The financing-vs-broker comparison is one table with color-grouped
column sections (shared / financing-only / broker-only), not two separate tables. Verified
rendering with headless Chrome screenshots (no project run-skill existed yet for this repo) -
confirmed the diagram loads, stats show real numbers, and both tables render correctly,
including the color-coded columns.

## 11. API-backed ingestion adapters

> Add a small FastAPI app in api/main.py with two endpoints, /sales-records and /debt-records,
> that just serve the rows from data/raw/sales_records.csv and data/raw/debt_records.csv as
> JSON. Then add new adapters, SalesAPIAdapter and DebtAPIAdapter, alongside the existing CSV
> adapters in ingestion/adapters/, same BaseSourceAdapter interface, but they call the API
> endpoints instead of reading the CSV directly. Ingestion, entity resolution, opportunity
> detection, and governance shouldn't need to change at all, they only ever see canonical
> records either way. Run it end to end with the API adapters and confirm the output matches
> the CSV version.

Added `api/main.py`. While doing this, discovered `SalesCSVAdapter`/`DebtCSVAdapter` actually
lived in `src/ingestion.py`, not in `ingestion/adapters/` - moved them into the package for
real, split into `csv_adapters.py` and `api_adapters.py` sharing the same `to_canonical` mixins
so the two transports can't silently normalize differently. `requests`/`fastapi`/`uvicorn`
went into a new optional `api` extra so a CSV-only install never needs them. Verified for real:
started the FastAPI server, ran ingestion with `--source api`, diffed the output against a
`--source csv` baseline (identical except the `ingested_at` timestamp), then ran entity
resolution and opportunity detection unmodified against the API-sourced data and got identical
counts to every prior CSV-sourced run.

## 12. Scale to 400 rows/file + zip-code blocking

> expand data/raw/sales_records.csv and debt_records.csv from 30 rows to 400 rows each, same
> messiness pattern as before... spread across at least 10-15 different zip codes so blocking
> actually has something to partition on and update entity_resolution/candidates.py so
> generate_candidate_pairs() blocks by zip code before scoring and only compare a Sales record
> against Debt records sharing the same zip, instead of every record against every record, Run
> pytest, run the pipeline end to end, and tell me how long entity resolution takes with and
> without blocking so I have real numbers and Also add prompts to prompts/ai_prompts_log.md

Wrote `scripts/generate_synthetic_data.py` - a seeded, reproducible generator (400 rows/file
across 15 zip codes: 130 "shared" entities at identical addresses, 20 deliberately "ambiguous"
entities sharing a zip but not a street, ~250 unique-to-one-side entities each) rather than
hand-authoring 800 rows. Updated `generate_candidate_pairs()` to block by the first 5 digits of
postal code before pairing across sources. Benchmarked with a new `scripts/benchmark_entity_resolution.py`
against the real 769 valid canonical records: **without blocking, 147,838 pairs in ~7.7-8.3s;
with blocking, 10,189 pairs in ~0.52-0.56s - about a 14.5x reduction in pairs and a ~14.7x
speedup**, with per-pair cost essentially unchanged (~52-56 us/pair either way, confirming the
gain is entirely from doing less work, not a faster scorer). Full test suite (93 tests) and the
full pipeline both run clean on the new dataset.

## 13. CORS + the React frontend

> Also add CORS so http://localhost:5173 is allowed to call the API then let's build the
> frontend. Scaffold a Vite + React app in frontend/. I want one single page, no tabs, no
> router just a clean scrolling page. Give it a commercial realestate feel: navy and gold,
> Playfair Display for headings by pulling it from Google Fonts, Inter for body text, cream
> background, cards with a subtle shadow instead of flat white everywhere. Header up top:
> "Cross-Silo Opportunity Engine" with a short subtitle underneath. Below that, show all four
> stages stacked one after another, connected by a numbered timeline like a stepper, each one
> in its own card: Ingestion - a button that calls POST /ingest?limit=20 (grab the raw counts
> from /sales-records and /debt-records first, same limit), then show the canonical records it
> produced in a table. Entity resolution - button calls POST /resolve-entities, show the
> matches with a confidence/outcome column, color-coded by outcome. Opportunity detection -
> button calls POST /detect-opportunities, show the ranked results. Governance - a role
> dropdown plus a button that calls GET /opportunities?role=X and shows the scoped result. Each
> stage should stay locked - button actually disabled, not just grayed out - until the one
> before it has successfully run. Dim the locked ones so it's obvious. If a call fails, show
> the error right there in that stage's card instead of failing silently. Once it's built, run
> both servers and walk through all four stages to make sure they actually work in order, and
> that switching the role in stage 4 really does change what fields show up.

Added `CORSMiddleware` to `api/main.py` allowing `http://localhost:5173`. Had to install
Node.js first - winget hung indefinitely for unclear reasons, so fetched the portable Node.js
binary directly instead. Scaffolded `frontend/` with `npm create vite@latest -- --template
react`, then wrote the real app: navy/gold palette sampled conceptually to match the existing
architecture-diagram colors, Playfair Display + Inter via Google Fonts, a numbered stepper of
four stacked cards, `disabled`-attribute locking, and per-card inline error boxes. Verified
with a real headless-browser walkthrough (not just code review): confirmed stage buttons were
genuinely `disabled` before their prerequisite ran, watched real data flow through all four
stages, and confirmed switching roles in stage 4 actually changes which fields render
(financing vs. broker vs. property_management each showed a different, correct field set).

## 14. README: frontend setup + run instructions

> In the setup section in read.me file add the react setup instructions and how to run the UI

Added a "Frontend (React UI)" subsection under Setup (Node requirement, `npm install`) and a
new "Run the UI" section mirroring the existing "Run the full pipeline"/"Run tests" style -
the two-terminal startup, the URL, and a walkthrough of what each stage card does.

## 15. Fix uvicorn 404 at /

> now lets fix the uvicorn [pasted terminal output showing GET / returning 404 Not Found]

Nothing was actually broken - the server started cleanly (confirming the `sys.path` fix from
the API-adapters work holds up in a fresh venv too), and the 404 was just FastAPI correctly
reporting that no route exists at `/` (only `/docs`, `/sales-records`, etc. are defined). Added
a `GET /` handler that redirects to `/docs`, verified live (`GET /` -> `307` -> `/docs` -> `200`).

## 16. Vertical scroll, generic copy, real batch cycling

> In the App.JS, the data table wrapper only scrolls horizontally right now. Add vertical
> scrolling too and also make the header sub header generic and also do not specify execution
> of twenty rows, and it only runs once right now. Whenever user clicks on run ingestion, pick
> the first ten records from both sales and debt, and then run the ingestion and normalization
> and the rest of the steps. So every click do the same and once all the records are finished
> and then circle it back.

Added `max-height` + `overflow-y: auto` (with a sticky header) to `.table-wrap`. Added
`offset` support to `/sales-records`, `/debt-records`, and `/ingest` on the backend (a
`_windowed()` helper and an offset-aware `_LimitedAdapter`), and a `cursor` in the frontend
that advances by 10 rows every click, wrapping back to 0 once both sources are exhausted.
Reworded stage 1's description to be generic (no hardcoded row count). Verified with 42
scripted clicks against the real 400-row dataset: batch start sequence went `1, 11, 21, ...,
391`, then wrapped straight back to `1` - confirmed circling through the full dataset, not
just re-running the same batch.

## 17. Tab layout

> Let's make all the four stages tab style, side by side, and first tab should be active, and
> the rest should be grayed out. And it should follow the same model as before of displaying
> and running one after the other and provide some [affordance] if the user wants to execute
> the next batch

Replaced the stacked-card stepper with a horizontal tab bar (tab 1 active by default, tabs
2-4 genuinely `disabled` until the stage before them succeeds, a checkmark on completed tabs).
Simplified `StageCard` to a plain panel since only the active tab's content ever renders.
Renamed the ingestion button to "Run Next Batch" and added a hint line showing the exact row
range the next click will process. Verified live: a forced click on a locked tab did nothing,
tabs unlocked in the correct order, and returning to tab 1 after visiting tab 2 and running
another batch still advanced correctly (proving state isn't lost on tab switches).

## 18. Widen the layout + spread tabs + catch up the docs

> two things. The page wheels too narrow and boxed in. Widen the content area so it uses more
> of the page like a real website, not a skinny centered column. Keep the header title and
> subtitles centered as they are, but spread the four stage steps even across leader full width
> instead of bunched and stack together on one side. Also, update the prompts log markdown
> file, append the prompts used to build the frontend. And also update the readme file to have
> the frontend setup and instructions for running the UI.

Widened `.app` from a 920px column to 1360px, capped the header subtitle at 640px so its line
length stays readable inside the wider page, and left the tab bar's existing `flex: 1` layout
alone - it was already built to spread evenly, it just had a narrow container to spread across.
Verified the four tabs now sit at equal ~317px widths spanning the full content area. Refreshed
README's "Run the UI" section (it still described the old fixed-limit-20, stacked-card
behavior) to match the tab layout and per-click batch cycling. Backfilled this log with
entries 13-17, which had accumulated without being recorded.
