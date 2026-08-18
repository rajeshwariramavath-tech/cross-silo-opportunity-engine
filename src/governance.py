"""Stage 4 — governance & access control, runnable end to end.

Reads data/processed/opportunities.csv (Stage 3's output) and, for a requesting role, returns
a filtered view of every opportunity: which fields that role gets is decided once, by the
role-to-field-permissions mapping in cross_silo_opportunity_engine.governance.permissions, and
applied the same way at every request - the same opportunity renders as a full record for one
role and a near-empty flag for another.

Every field that IS returned carries its own source_system/source_id lineage (see
cross_silo_opportunity_engine.governance.lineage.trace_field), so scoping down what a role
sees never breaks the ability to trace a number back to the exact record it came from.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from cross_silo_opportunity_engine.governance.access_control import scope_result
from cross_silo_opportunity_engine.governance.roles import Role

REPO_ROOT = Path(__file__).resolve().parent.parent
OPPORTUNITIES_PATH = REPO_ROOT / "data" / "processed" / "opportunities.csv"


def load_opportunities(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        opportunities = []
        for row in csv.DictReader(handle):
            row["composite_score"] = int(row["composite_score"]) if row["composite_score"] else None
            row["entity_resolution_confidence"] = (
                float(row["entity_resolution_confidence"]) if row["entity_resolution_confidence"] else None
            )
            row["fired_rules"] = row["fired_rules"].split("; ") if row["fired_rules"] else []
            opportunities.append(row)
        return opportunities


def get_opportunities_for_role(opportunities: list[dict[str, Any]], role: Role) -> list[dict[str, Any]]:
    """The reusable entry point: opportunities + a requesting role -> a filtered view."""
    return [scope_result(opportunity, role) for opportunity in opportunities]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", required=True, choices=[role.value for role in Role])
    args = parser.parse_args()

    opportunities = load_opportunities(OPPORTUNITIES_PATH)
    scoped = get_opportunities_for_role(opportunities, Role(args.role))
    print(json.dumps(scoped, indent=2))


if __name__ == "__main__":
    main()
