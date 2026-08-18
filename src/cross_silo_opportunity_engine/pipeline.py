"""Wires the four stages together: ingestion -> entity resolution -> opportunity detection -> governance.

Each stage's own module (src/ingestion.py, src/entity_resolution.py, src/opportunity_detection.py,
src/governance.py) already does the real work and is independently runnable; this module only
sequences them, the same way running the four scripts by hand would - read the upstream CSV,
call the stage's existing functions, write the downstream CSV, hand off to the next stage.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

# These are the top-level, runnable stage scripts under src/ (src/ingestion.py, etc.) - not
# the cross_silo_opportunity_engine.* subpackages of the same name. They're importable here
# because the editable install puts src/ on sys.path; aliased to keep that distinction clear.
import entity_resolution as entity_resolution_stage
import governance as governance_stage
import ingestion as ingestion_stage
import opportunity_detection as opportunity_detection_stage

from .governance.roles import Role

PROCESSED_DIR = ingestion_stage.PROCESSED_DIR


def run_pipeline(requesting_role: Role) -> list[dict[str, Any]]:
    """Runs all four stages in order and returns the final opportunity list, scoped to
    requesting_role. Also leaves the same intermediate CSVs in data/processed/ that running
    each stage script separately would."""
    adapters = [
        (ingestion_stage.SalesCSVAdapter(ingestion_stage.RAW_DIR / "sales_records.csv"), ingestion_stage.SALES_REQUIRED_RAW_FIELDS),
        (ingestion_stage.DebtCSVAdapter(ingestion_stage.RAW_DIR / "debt_records.csv"), ingestion_stage.DEBT_REQUIRED_RAW_FIELDS),
    ]
    canonical_records, rejected_rows = ingestion_stage.run_ingestion(adapters)
    ingestion_stage.write_canonical_records(canonical_records, PROCESSED_DIR / "canonical_records.csv")
    ingestion_stage.write_rejects(rejected_rows, PROCESSED_DIR / "ingestion_rejects.csv")

    matches = entity_resolution_stage.run_entity_resolution(canonical_records)
    entity_resolution_stage.write_matches(matches, PROCESSED_DIR / "entity_matches.csv")

    canonical_lookup = opportunity_detection_stage.load_canonical_lookup(PROCESSED_DIR / "canonical_records.csv")
    resolved_matches = [match for match in matches if match["outcome"] == "auto_match"]
    opportunities = opportunity_detection_stage.run_opportunity_detection(resolved_matches, canonical_lookup)
    opportunity_detection_stage.write_opportunities(opportunities, PROCESSED_DIR / "opportunities.csv")

    return governance_stage.get_opportunities_for_role(opportunities, requesting_role)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=[role.value for role in Role])
    args = parser.parse_args()

    scoped = run_pipeline(Role(args.role))
    print(json.dumps(scoped, indent=2, default=str))


if __name__ == "__main__":
    main()
