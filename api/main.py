"""HTTP surface over the four pipeline stages.

Every endpoint below is a thin wrapper: it calls the same load/run/write functions the
command-line stage scripts (src/ingestion.py, src/entity_resolution.py,
src/opportunity_detection.py, src/governance.py, cross_silo_opportunity_engine/pipeline.py)
already call, and returns the result as JSON. No pipeline logic lives here - GET /sales-records
and /debt-records also stand in for the sales and debt systems' own internal APIs, which
SalesAPIAdapter/DebtAPIAdapter (ingestion/adapters/api_adapters.py) consume the same way they'd
consume a real source system's API.

Run with: uvicorn api.main:app --port 8000
Then open http://127.0.0.1:8000/docs for interactive Swagger UI.
"""

from __future__ import annotations

import csv
import dataclasses
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"

# src/ has to be importable for the two imports below - both the top-level stage scripts
# (ingestion.py, entity_resolution.py, opportunity_detection.py) and the
# cross_silo_opportunity_engine package live there. Don't rely on an editable install having
# been run (its sys.path side effect can be absent - a different Python/venv than the one
# `pip install -e .` ran in, uvicorn's own reload subprocess, a fresh checkout) or on a
# PYTHONPATH env var: resolve it relative to this file so `uvicorn api.main:app` works from a
# clean shell every time.
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Top-level pipeline stage scripts under src/ (src/ingestion.py, etc.) - not the
# cross_silo_opportunity_engine.* subpackages of the same name. Aliased to keep that
# distinction unambiguous.
import entity_resolution as entity_resolution_stage  # noqa: E402
import ingestion as ingestion_stage  # noqa: E402
import opportunity_detection as opportunity_detection_stage  # noqa: E402
from cross_silo_opportunity_engine.governance.roles import Role  # noqa: E402
from cross_silo_opportunity_engine.pipeline import run_pipeline  # noqa: E402

app = FastAPI(
    title="Cross-Silo Opportunity Engine API",
    description="HTTP surface over the four pipeline stages: ingestion, entity resolution, "
    "opportunity detection, and governance.",
)


def _read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _require(path: Path, upstream_endpoint: str) -> None:
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"{path.name} not found - call {upstream_endpoint} first.")


@app.get("/sales-records")
def sales_records() -> list[dict[str, Any]]:
    """Raw sales-system rows, straight from data/raw/sales_records.csv, as JSON.

    Stands in for the sales system's own API - SalesAPIAdapter consumes this exact endpoint.
    """
    return _read_csv_rows(RAW_DIR / "sales_records.csv")


@app.get("/debt-records")
def debt_records() -> list[dict[str, Any]]:
    """Raw debt-system rows, straight from data/raw/debt_records.csv, as JSON.

    Stands in for the debt system's own API - DebtAPIAdapter consumes this exact endpoint.
    """
    return _read_csv_rows(RAW_DIR / "debt_records.csv")


@app.post("/ingest")
def ingest() -> dict[str, Any]:
    """Runs Stage 1 (ingestion & normalization).

    Reads both raw CSVs, normalizes every record into the shared canonical schema, flags
    invalid rows instead of dropping them, writes data/processed/canonical_records.csv and
    ingestion_rejects.csv, and returns the canonical records. Calls
    ingestion.run_ingestion() - the same function the ingestion.py CLI runs.
    """
    adapters = ingestion_stage.build_adapters("csv", ingestion_stage.DEFAULT_API_BASE_URL)
    canonical_records, rejected_rows = ingestion_stage.run_ingestion(adapters)
    ingestion_stage.write_canonical_records(canonical_records, ingestion_stage.PROCESSED_DIR / "canonical_records.csv")
    ingestion_stage.write_rejects(rejected_rows, ingestion_stage.PROCESSED_DIR / "ingestion_rejects.csv")
    return {
        "canonical_record_count": len(canonical_records),
        "rejected_count": len(rejected_rows),
        "canonical_records": [dataclasses.asdict(record) for record in canonical_records],
    }


@app.post("/resolve-entities")
def resolve_entities() -> dict[str, Any]:
    """Runs Stage 2 (entity resolution). Call POST /ingest first.

    Reads data/processed/canonical_records.csv, scores every zip-blocked candidate pair on
    address/name/geography similarity, writes data/processed/entity_matches.csv, and returns
    every scored pair with its confidence score and outcome bucket (auto_match / review_queue
    / auto_reject). Calls entity_resolution.run_entity_resolution() - the same function the
    entity_resolution.py CLI runs.
    """
    _require(entity_resolution_stage.CANONICAL_RECORDS_PATH, "POST /ingest")
    records = entity_resolution_stage.load_canonical_records(entity_resolution_stage.CANONICAL_RECORDS_PATH)
    matches = entity_resolution_stage.run_entity_resolution(records)
    entity_resolution_stage.write_matches(matches, entity_resolution_stage.ENTITY_MATCHES_PATH)
    return {"pair_count": len(matches), "matches": matches}


@app.post("/detect-opportunities")
def detect_opportunities() -> dict[str, Any]:
    """Runs Stage 3 (opportunity detection). Call POST /ingest and POST /resolve-entities first.

    Takes the auto-matched pairs from data/processed/entity_matches.csv, runs each through
    the deterministic business rules, writes data/processed/opportunities.csv, and returns the
    ranked, qualifying opportunities. Calls opportunity_detection.run_opportunity_detection() -
    the same function the opportunity_detection.py CLI runs (without the optional
    --rationale LLM step).
    """
    _require(opportunity_detection_stage.CANONICAL_RECORDS_PATH, "POST /ingest")
    _require(opportunity_detection_stage.ENTITY_MATCHES_PATH, "POST /resolve-entities")
    canonical_lookup = opportunity_detection_stage.load_canonical_lookup(opportunity_detection_stage.CANONICAL_RECORDS_PATH)
    matches = opportunity_detection_stage.load_resolved_matches(opportunity_detection_stage.ENTITY_MATCHES_PATH)
    opportunities = opportunity_detection_stage.run_opportunity_detection(matches, canonical_lookup)
    opportunity_detection_stage.write_opportunities(opportunities, opportunity_detection_stage.OPPORTUNITIES_PATH)

    # Each opportunity dict also carries internal rule-evaluation fields (_sale_value, etc.)
    # that write_opportunities() already excludes from the CSV via the same fieldname
    # allowlist - apply it here too so the API doesn't leak those past the public shape.
    public_fields = opportunity_detection_stage.OPPORTUNITY_FIELDNAMES
    public_opportunities = [{field: opp[field] for field in public_fields if field in opp} for opp in opportunities]
    return {"opportunity_count": len(public_opportunities), "opportunities": public_opportunities}


@app.get("/opportunities")
def opportunities_for_role(role: Role) -> dict[str, Any]:
    """Runs the full four-stage pipeline end to end and returns the opportunity list scoped
    to the given role.

    Equivalent to `python -m cross_silo_opportunity_engine.pipeline --role <role>` - calls
    pipeline.run_pipeline(), which re-runs ingestion, entity resolution, and opportunity
    detection from scratch and then applies governance.get_opportunities_for_role(). Try
    role=financing or role=broker to see the same opportunities rendered differently.
    """
    scoped = run_pipeline(role)
    return {"role": role.value, "count": len(scoped), "opportunities": scoped}
