"""Stage 3 — opportunity detection, runnable end to end.

Reads data/processed/entity_matches.csv (Stage 2's output) and data/processed/canonical_records.csv
(Stage 1's output), takes only the auto-matched resolved pairs, and runs each through explicit,
deterministic rules - not a model - so any flag can be traced back to the exact condition that
fired. Qualifying opportunities are ranked by a composite of those rules and written to
data/processed/opportunities.csv.

An optional --rationale pass can follow: one grounded, plain-language sentence per opportunity
via the Anthropic API (see generate_rationale in the package's opportunity_detection.explanation
module). It runs strictly after ranking and qualification are final and never feeds back into
either - if it's skipped or a call fails, the same opportunities come out in the same order,
just without a "rationale" value.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
from pathlib import Path
from typing import Any

from cross_silo_opportunity_engine.config import (
    LOAN_MATURITY_URGENCY_MONTHS,
    OPPORTUNITY_MIN_VALUE_THRESHOLD,
    OPPORTUNITY_RULE_WEIGHTS,
    STRONG_RELATIONSHIP_CONFIDENCE,
)
from cross_silo_opportunity_engine.opportunity_detection.explanation import generate_rationale
from cross_silo_opportunity_engine.opportunity_detection.ranking import rank_opportunities
from cross_silo_opportunity_engine.opportunity_detection.rules import Rule, evaluate_rules

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
ENTITY_MATCHES_PATH = PROCESSED_DIR / "entity_matches.csv"
CANONICAL_RECORDS_PATH = PROCESSED_DIR / "canonical_records.csv"
OPPORTUNITIES_PATH = PROCESSED_DIR / "opportunities.csv"

OPPORTUNITY_FIELDNAMES = [
    "entity_name",
    "sales_source_system", "sales_source_id",
    "debt_source_system", "debt_source_id",
    "sale_price", "close_date", "broker_name", "property_type",
    "loan_amount", "orig_date", "maturity_date", "lender_name", "loan_type", "notes",
    "entity_resolution_confidence", "fired_rules", "composite_score", "rationale",
]


def load_canonical_lookup(csv_path: Path) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            lookup[(row["source_system"], row["source_record_id"])] = row
    return lookup


def load_resolved_matches(csv_path: Path) -> list[dict[str, Any]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return [row for row in csv.DictReader(handle) if row["outcome"] == "auto_match"]


def _parse_currency(raw: str) -> float | None:
    if not raw:
        return None
    cleaned = raw.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_date(raw: str) -> date | None:
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def build_opportunity(match: dict[str, Any], canonical_lookup: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any] | None:
    sides = [
        (match["source_system_a"], match["source_id_a"]),
        (match["source_system_b"], match["source_id_b"]),
    ]
    sales_key = next((s for s in sides if s[0] == "sales_records"), None)
    debt_key = next((s for s in sides if s[0] == "debt_records"), None)
    if sales_key is None or debt_key is None:
        return None

    sales_row = canonical_lookup.get(sales_key)
    debt_row = canonical_lookup.get(debt_key)
    if sales_row is None or debt_row is None:
        return None

    return {
        "entity_name": sales_row["entity_name"],
        "sales_source_system": sales_row["source_system"],
        "sales_source_id": sales_row["source_record_id"],
        "debt_source_system": debt_row["source_system"],
        "debt_source_id": debt_row["source_record_id"],
        "sale_price": sales_row["extra_sale_price"],
        "close_date": sales_row["extra_close_date"],
        "broker_name": sales_row["extra_broker_name"],
        "property_type": sales_row["extra_property_type"],
        "loan_amount": debt_row["extra_loan_amount"],
        "orig_date": debt_row["extra_orig_date"],
        "maturity_date": debt_row["extra_maturity_date"],
        "lender_name": debt_row["extra_lender_name"],
        "loan_type": debt_row["extra_loan_type"],
        "notes": debt_row["extra_notes"],
        "entity_resolution_confidence": float(match["confidence"]),
        "_sale_value": _parse_currency(sales_row["extra_sale_price"]),
        "_loan_value": _parse_currency(debt_row["extra_loan_amount"]),
        "_maturity_date": _parse_date(debt_row["extra_maturity_date"]),
        "_notes_lower": (debt_row["extra_notes"] or "").lower(),
    }


def build_rules(today: date) -> list[Rule]:
    maturity_cutoff_days = LOAN_MATURITY_URGENCY_MONTHS * 30

    return [
        Rule(
            "high_value_deal",
            lambda o: (o["_sale_value"] or 0) >= OPPORTUNITY_MIN_VALUE_THRESHOLD
            or (o["_loan_value"] or 0) >= OPPORTUNITY_MIN_VALUE_THRESHOLD,
        ),
        Rule("loan_past_due", lambda o: "past due" in o["_notes_lower"]),
        Rule(
            "loan_maturing_soon",
            lambda o: o["_maturity_date"] is not None
            and 0 <= (o["_maturity_date"] - today).days <= maturity_cutoff_days,
        ),
        Rule(
            "strong_relationship_match",
            lambda o: o["entity_resolution_confidence"] >= STRONG_RELATIONSHIP_CONFIDENCE,
        ),
    ]


def run_opportunity_detection(
    matches: list[dict[str, Any]],
    canonical_lookup: dict[tuple[str, str], dict[str, Any]],
    today: date | None = None,
) -> list[dict[str, Any]]:
    rules = build_rules(today or date.today())
    opportunities = []

    for match in matches:
        opportunity = build_opportunity(match, canonical_lookup)
        if opportunity is None:
            continue

        fired_rules = evaluate_rules(opportunity, rules)
        if not fired_rules:
            continue

        opportunity["fired_rules"] = fired_rules
        opportunity["composite_score"] = sum(OPPORTUNITY_RULE_WEIGHTS[name] for name in fired_rules)
        opportunities.append(opportunity)

    return rank_opportunities(opportunities)


def attach_rationales(opportunities: list[dict[str, Any]]) -> None:
    """Runs strictly after ranking - adds text in place, never reorders or filters."""
    for opportunity in opportunities:
        opportunity["rationale"] = generate_rationale(opportunity, opportunity["fired_rules"])


def write_opportunities(opportunities: list[dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OPPORTUNITY_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for opportunity in opportunities:
            row = dict(opportunity)
            row["fired_rules"] = "; ".join(opportunity["fired_rules"])
            row.setdefault("rationale", "")
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rationale",
        action="store_true",
        help="Also call the Anthropic API for a one-sentence rationale per opportunity.",
    )
    args = parser.parse_args()

    canonical_lookup = load_canonical_lookup(CANONICAL_RECORDS_PATH)
    matches = load_resolved_matches(ENTITY_MATCHES_PATH)
    opportunities = run_opportunity_detection(matches, canonical_lookup)

    if args.rationale:
        attach_rationales(opportunities)

    write_opportunities(opportunities, OPPORTUNITIES_PATH)
    print(f"resolved matches: {len(matches)}, opportunities: {len(opportunities)}")


if __name__ == "__main__":
    main()
