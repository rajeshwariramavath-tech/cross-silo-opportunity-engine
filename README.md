# cross-silo-opportunity-engine

[![CI](https://github.com/rajeshwariramavath-tech/cross-silo-opportunity-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/rajeshwariramavath-tech/cross-silo-opportunity-engine/actions)

Connects data across siloed commercial real estate lines of business so cross-business
opportunities surface automatically, without giving anyone unrestricted access to sensitive
data they shouldn't see.

**Architecture:** [docs/architecture.md](docs/architecture.md)

The three processing stages - ingestion & normalization, entity resolution, and opportunity
detection - run end to end through `pipeline.py`, with governance & access control applied as
a boundary around all three, enforced at the point a result is served.

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
├── governance.py              # Governance entry point - role-scoped CLI view
└── cross_silo_opportunity_engine/
    ├── ingestion/              # Canonical schema, normalization, adapter interface
    ├── entity_resolution/      # Signals, scoring, three-outcome classification
    ├── opportunity_detection/  # Rules, ranking, optional LLM rationale
    ├── governance/             # Roles, field permissions, access control - a boundary, not a stage
    ├── pipeline.py             # Wires the three stages together, with a CLI
    └── config.py               # Shared thresholds and weights
api/main.py                     # FastAPI app: HTTP surface over the three stages + governance
frontend/                       # Vite + React UI - single page, tab layout, calls the API
tests/                          # Tests for the three stages and governance, package and entry points alike
prompts/ai_prompts_log.md       # Log of the prompts used to build this project
```

## Setup

**Prerequisites:** Python 3.10+ and [Node.js](https://nodejs.org/) 18+.

### 1. Backend

Install the package. Pick the extras you need:

| Command | Adds |
|---|---|
| `pip install -e ".[dev]"` | Core + test dependencies (default) |
| `pip install -e ".[dev,llm]"` | + Anthropic SDK, for `opportunity_detection`'s `--rationale` |
| `pip install -e ".[dev,llm,api]"` | + FastAPI/uvicorn/requests, for `api/main.py` |

Verify it's working:

```
uvicorn api.main:app --port 8000
```

Open http://127.0.0.1:8000/docs — you should see the interactive Swagger UI.

### 2. Frontend

```
cd frontend
npm install
```

Setup's done — see [Usage](#usage) below to run the pipeline, the API, and the UI together.

## Usage

### Run the pipeline

```
python -m cross_silo_opportunity_engine.pipeline --role <role>
```

`<role>` is one of `admin`, `broker`, `financing`, `valuation`, `property_management`. Prints
the final, role-scoped opportunity list as JSON and leaves each stage's intermediate CSV in
`data/processed/`.

### Run the app

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

### Run tests

```
pytest
```

Tests cover the three processing stages and governance - the generic package modules and the
concrete entry-point scripts alike.

## How this was built

See [prompts/ai_prompts_log.md](prompts/ai_prompts_log.md) for the prompt-by-prompt history.