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
pip install -e ".[dev]"          # core + test dependencies
pip install -e ".[dev,llm]"      # add the Anthropic SDK for opportunity_detection's --rationale
pip install -e ".[dev,llm,api]"  # add FastAPI/uvicorn/requests for api/main.py
```

### Frontend (React UI)

Requires [Node.js](https://nodejs.org/) 18+.

```
cd frontend
npm install
```

## Run the full pipeline

```
python -m cross_silo_opportunity_engine.pipeline --role <role>
```

`<role>` is one of `admin`, `broker`, `financing`, `valuation`, `property_management`. Prints
the final, role-scoped opportunity list as JSON and leaves each stage's intermediate CSV in
`data/processed/`.

## Run the app

The frontend drives the pipeline through the API, so both servers need to be running.

```
# terminal 1 - API (from the repo root)
uvicorn api.main:app --port 8000

# terminal 2 - frontend
cd frontend
npm run dev
```

Then open http://localhost:5173. Four stage tabs run left to right; each stays disabled until
the one before it succeeds, and a checkmark appears on a tab once it's done:

The API's CORS policy only allows `http://localhost:5173`, so run the frontend on Vite's
default port.

## Run tests

```
pytest
```

Tests cover all four stages - the generic package modules and the concrete entry-point
scripts alike.

## How this was built

See [prompts/ai_prompts_log.md](prompts/ai_prompts_log.md) for the prompt-by-prompt history.
