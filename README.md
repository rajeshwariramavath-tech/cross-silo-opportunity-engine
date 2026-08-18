# cross-silo-opportunity-engine

Connects data across siloed commercial real estate lines of business so cross-business
opportunities surface automatically, without giving anyone unrestricted access to sensitive
data they shouldn't see. See [docs/architecture.md](docs/architecture.md) for the full design.

## Structure

The package mirrors the four-stage pipeline described in the architecture doc:

```
src/cross_silo_opportunity_engine/
├── ingestion/              # Stage 1 — per-source adapters into one canonical shape
│   └── adapters/           # One adapter per source system
├── entity_resolution/      # Stage 2 — signal scoring, auto-match/review/auto-reject
├── opportunity_detection/  # Stage 3 — auditable rules, ranking, optional LLM explanation
├── governance/             # Stage 4 — role-scoped delivery, field-level lineage
├── pipeline.py             # Wires the four stages together end to end
└── config.py                # Shared thresholds and weights
tests/                       # Mirrors the package layout above
```

## Setup

```
pip install -e ".[dev]"
pytest
```