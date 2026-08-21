"""Builds docs/report.html: a single self-contained page summarizing a pipeline run.

Reads the CSVs already sitting in data/processed/ (run the pipeline first - see
`python -m cross_silo_opportunity_engine.pipeline --role <role>` in the README) and renders,
top to bottom: the architecture diagram, summary stats for each stage, the full ranked
opportunities list, and a side-by-side governance comparison of the financing vs. broker
views of the same opportunities. The comparison calls the real governance code
(governance.get_opportunities_for_role) rather than re-deriving who-sees-what - the field
groupings in that table come straight from ROLE_FIELD_PERMISSIONS.

No external CSS/JS/fonts and no build step - the HTML references docs/architecture.png by a
relative path (it already lives next to this file's output), so the page opens directly from
disk and renders the same way on GitHub Pages.
"""

from __future__ import annotations

import csv
import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import governance
from cross_silo_opportunity_engine.governance.permissions import ROLE_FIELD_PERMISSIONS
from cross_silo_opportunity_engine.governance.roles import Role

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
DOCS_DIR = REPO_ROOT / "docs"
REPORT_PATH = DOCS_DIR / "report.html"

# Sampled from docs/architecture.png so the report reads as part of the same document.
GREEN = {"bg": "#E3F6EE", "border": "#1F8A63", "text": "#0E6B4A"}    # Stage 1/2, auto-match
AMBER = {"bg": "#FBF0D3", "border": "#A67C00", "text": "#7A5C00"}    # Review queue
RED = {"bg": "#FCE4E1", "border": "#B33A3A", "text": "#A13030"}      # Auto-reject
RUST = {"bg": "#FCEADD", "border": "#C1531F", "text": "#A8431B"}     # Stage 3
PURPLE = {"bg": "#EEEAFB", "border": "#4A3F91", "text": "#3D3480"}   # Governance
BEIGE = {"bg": "#EFECE2", "border": "#8A8578", "text": "#4A4640"}    # Source systems

CANONICAL_FIELD_ORDER = [
    "entity_name", "property_type", "entity_resolution_confidence", "fired_rules", "composite_score",
    "sale_price", "close_date", "broker_name",
    "loan_amount", "orig_date", "maturity_date", "lender_name", "loan_type", "notes",
]

FIELD_LABELS = {
    "property_type": "Property Type",
    "entity_resolution_confidence": "Confidence",
    "fired_rules": "Fired Rules",
    "composite_score": "Score",
    "sale_price": "Sale Price",
    "close_date": "Close Date",
    "broker_name": "Broker",
    "loan_amount": "Loan Amount",
    "orig_date": "Orig. Date",
    "maturity_date": "Maturity Date",
    "lender_name": "Lender",
    "loan_type": "Loan Type",
    "notes": "Notes",
}


def read_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def format_currency(raw: Any) -> str:
    if not raw:
        return "—"
    raw = str(raw)
    if raw.startswith("$"):
        return raw
    try:
        return f"${int(float(raw)):,}"
    except ValueError:
        return raw


def format_rules(rules: Any) -> str:
    if not rules:
        return "—"
    if isinstance(rules, str):
        rules = [r for r in rules.split(";") if r.strip()]
    return ", ".join(r.strip().replace("_", " ").title() for r in rules)


def format_confidence(value: Any) -> str:
    if value in (None, ""):
        return "—"
    try:
        return f"{float(value):.2f}"
    except ValueError:
        return str(value)


# --------------------------------------------------------------------------- stats


def build_summary_stats() -> dict[str, Any]:
    canonical_rows = read_csv_rows(PROCESSED_DIR / "canonical_records.csv")
    reject_rows = read_csv_rows(PROCESSED_DIR / "ingestion_rejects.csv")
    match_rows = read_csv_rows(PROCESSED_DIR / "entity_matches.csv")
    opportunity_rows = read_csv_rows(PROCESSED_DIR / "opportunities.csv")

    by_source: dict[str, int] = {}
    for row in canonical_rows:
        by_source[row["source_system"]] = by_source.get(row["source_system"], 0) + 1

    outcome_counts: dict[str, int] = {}
    for row in match_rows:
        outcome_counts[row["outcome"]] = outcome_counts.get(row["outcome"], 0) + 1

    return {
        "canonical_total": len(canonical_rows),
        "canonical_by_source": by_source,
        "reject_total": len(reject_rows),
        "match_total": len(match_rows),
        "auto_match": outcome_counts.get("auto_match", 0),
        "review_queue": outcome_counts.get("review_queue", 0),
        "auto_reject": outcome_counts.get("auto_reject", 0),
        "opportunity_total": len(opportunity_rows),
    }


# --------------------------------------------------------------------------- HTML fragments


def render_stat_card(label: str, value: Any, palette: dict[str, str], sub: str = "") -> str:
    sub_html = f'<div class="stat-sub">{esc(sub)}</div>' if sub else ""
    return f"""
    <div class="stat-card" style="background:{palette['bg']};border-color:{palette['border']}">
      <div class="stat-value" style="color:{palette['text']}">{esc(value)}</div>
      <div class="stat-label">{esc(label)}</div>
      {sub_html}
    </div>"""


def render_summary_section(stats: dict[str, Any]) -> str:
    sales_n = stats["canonical_by_source"].get("sales_records", 0)
    debt_n = stats["canonical_by_source"].get("debt_records", 0)
    cards = "".join([
        render_stat_card("Canonical Records", stats["canonical_total"], GREEN, f"{sales_n} sales · {debt_n} debt"),
        render_stat_card("Ingestion Rejects", stats["reject_total"], RED, "flagged, not dropped"),
        render_stat_card("Auto-Match", stats["auto_match"], GREEN, f"of {stats['match_total']} pairs scored"),
        render_stat_card("Review Queue", stats["review_queue"], AMBER, "ambiguous, sent to a human"),
        render_stat_card("Auto-Reject", stats["auto_reject"], RED, "confidently not a match"),
        render_stat_card("Opportunities", stats["opportunity_total"], RUST, f"of {stats['auto_match']} resolved matches"),
    ])
    return f'<section class="stats-row">{cards}</section>'


def render_opportunities_table(opportunity_rows: list[dict[str, Any]]) -> str:
    header_cells = "".join(
        f"<th>{esc(FIELD_LABELS.get(f, f.replace('_', ' ').title()))}</th>"
        for f in ["entity_name", "property_type", "sale_price", "loan_amount", "maturity_date",
                  "notes", "entity_resolution_confidence", "fired_rules", "composite_score"]
    )
    body_rows = []
    for rank, row in enumerate(opportunity_rows, start=1):
        cells = [
            f"<td class='rank-cell'>{rank}</td>",
            f"<td class='entity-cell'>{esc(row['entity_name'])}"
            f"<span class='lineage-note'>{esc(row['sales_source_id'])} · {esc(row['debt_source_id'])}</span></td>",
            f"<td>{esc(row['property_type'])}</td>",
            f"<td>{format_currency(row['sale_price'])}</td>",
            f"<td>{format_currency(row['loan_amount'])}</td>",
            f"<td>{esc(row['maturity_date']) or '—'}</td>",
            f"<td>{esc(row['notes']) or '—'}</td>",
            f"<td>{format_confidence(row['entity_resolution_confidence'])}</td>",
            f"<td>{format_rules(row['fired_rules'])}</td>",
            f"<td class='score-cell'>{esc(row['composite_score'])}</td>",
        ]
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    return f"""
    <table class="report-table">
      <thead><tr>{header_cells}</tr></thead>
      <tbody>{''.join(body_rows)}</tbody>
    </table>"""


def render_governance_comparison(opportunities: list[dict[str, Any]], financing_view: list[dict[str, Any]], broker_view: list[dict[str, Any]]) -> str:
    financing_fields = ROLE_FIELD_PERMISSIONS[Role.FINANCING]
    broker_fields = ROLE_FIELD_PERMISSIONS[Role.BROKER]
    shared = [f for f in CANONICAL_FIELD_ORDER if f in financing_fields and f in broker_fields and f != "entity_name"]
    financing_only = [f for f in CANONICAL_FIELD_ORDER if f in financing_fields and f not in broker_fields]
    broker_only = [f for f in CANONICAL_FIELD_ORDER if f in broker_fields and f not in financing_fields]

    def label_cells(fields: list[str]) -> str:
        return "".join(f"<th>{esc(FIELD_LABELS.get(f, f.title()))}</th>" for f in fields)

    def value(view_row: dict[str, Any], field: str) -> str:
        if field not in view_row:
            return "<span class='restricted'>restricted</span>"
        raw = view_row[field]
        if field in ("sale_price", "loan_amount"):
            return format_currency(raw)
        if field == "fired_rules":
            return format_rules(raw)
        if field == "entity_resolution_confidence":
            return format_confidence(raw)
        return esc(raw) if raw not in (None, "") else "—"

    header_group = (
        f"<tr class='group-row'>"
        f"<th colspan='2'></th>"
        f"<th colspan='{len(shared)}' class='group-shared'>Both roles see</th>"
        f"<th colspan='{len(financing_only)}' class='group-financing'>Financing sees</th>"
        f"<th colspan='{len(broker_only)}' class='group-broker'>Broker sees</th>"
        f"</tr>"
    )
    header_fields = (
        f"<tr><th>Rank</th><th>Entity</th>"
        f"{label_cells(shared)}{label_cells(financing_only)}{label_cells(broker_only)}</tr>"
    )

    body_rows = []
    for rank, (opp, fin, brk) in enumerate(zip(opportunities, financing_view, broker_view), start=1):
        cells = [f"<td class='rank-cell'>{rank}</td>"]
        cells.append(
            f"<td class='entity-cell'>{esc(opp['entity_name'])}"
            f"<span class='lineage-note'>{esc(opp['sales_source_id'])} · {esc(opp['debt_source_id'])}</span></td>"
        )
        for f in shared:
            cells.append(f"<td class='shared-cell'>{value(fin, f)}</td>")
        for f in financing_only:
            cells.append(f"<td class='financing-cell'>{value(fin, f)}</td>")
        for f in broker_only:
            cells.append(f"<td class='broker-cell'>{value(brk, f)}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")

    return f"""
    <div class="table-scroll">
    <table class="report-table governance-table">
      <thead>{header_group}{header_fields}</thead>
      <tbody>{''.join(body_rows)}</tbody>
    </table>
    </div>"""


# --------------------------------------------------------------------------- page shell


def render_page(stats: dict[str, Any], opportunities_table_html: str, governance_table_html: str) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Cross-Silo Opportunity Engine — Pipeline Report</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --page-bg: #FAFAF8;
    --card-bg: #FFFFFF;
    --border: #E3E1DA;
    --text: #2B2A28;
    --muted: #746F66;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 40px 24px 80px;
    background: var(--page-bg);
    color: var(--text);
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5;
  }}
  .container {{ max-width: 1180px; margin: 0 auto; }}
  header.page-header {{ text-align: center; margin-bottom: 32px; }}
  header.page-header h1 {{ font-size: 1.9rem; margin: 0 0 6px; }}
  header.page-header p {{ color: var(--muted); margin: 0; font-size: 0.95rem; }}

  .card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 32px;
  }}
  .diagram-card {{ text-align: center; padding: 16px; }}
  .diagram-card img {{ max-width: 100%; height: auto; border-radius: 6px; }}
  .diagram-card figcaption {{ color: var(--muted); font-size: 0.85rem; margin-top: 10px; }}

  .opportunities-card {{ border-top: 4px solid {RUST['border']}; }}
  .opportunities-card h2 {{ color: {RUST['text']}; }}
  .governance-card {{ border-top: 4px solid {PURPLE['border']}; }}
  .governance-card h2 {{ color: {PURPLE['text']}; }}

  section h2 {{ font-size: 1.25rem; margin: 0 0 4px; }}
  section .section-note {{ color: var(--muted); font-size: 0.9rem; margin: 0 0 16px; }}

  .stats-row {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 14px;
    margin-bottom: 36px;
  }}
  .stat-card {{
    border: 1px solid;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
  }}
  .stat-value {{ font-size: 1.8rem; font-weight: 700; }}
  .stat-label {{ font-size: 0.85rem; font-weight: 600; margin-top: 2px; }}
  .stat-sub {{ font-size: 0.75rem; color: var(--muted); margin-top: 4px; }}

  table.report-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.87rem;
  }}
  .report-table th, .report-table td {{
    padding: 9px 10px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    white-space: nowrap;
  }}
  .report-table thead th {{
    background: #F4F3EF;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--muted);
  }}
  .rank-cell {{ color: var(--muted); font-variant-numeric: tabular-nums; }}
  .score-cell {{ font-weight: 700; }}
  .entity-cell {{ display: flex; flex-direction: column; white-space: normal; min-width: 150px; }}
  .lineage-note {{ font-size: 0.72rem; color: var(--muted); font-family: ui-monospace, Consolas, monospace; }}

  .table-scroll {{ overflow-x: auto; }}
  .governance-table .group-shared {{ background: #F4F3EF; color: var(--muted); }}
  .governance-table .group-financing {{ background: {GREEN['bg']}; color: {GREEN['text']}; }}
  .governance-table .group-broker {{ background: {RUST['bg']}; color: {RUST['text']}; }}
  .governance-table .group-row th {{
    text-align: center;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    border-bottom: none;
  }}
  .governance-table td.financing-cell {{ background: {GREEN['bg']}44; border-left: 2px solid {GREEN['border']}; }}
  .governance-table td.broker-cell {{ background: {RUST['bg']}66; border-left: 2px solid {RUST['border']}; }}
  .governance-table td.shared-cell {{ color: var(--muted); }}
  .restricted {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #B33A3A;
    opacity: 0.75;
  }}

  footer {{ text-align: center; color: var(--muted); font-size: 0.8rem; margin-top: 40px; }}
</style>
</head>
<body>
<div class="container">

  <header class="page-header">
    <h1>Cross-Silo Opportunity Engine</h1>
    <p>Pipeline report · generated {esc(generated_at)}</p>
  </header>

  <figure class="card diagram-card">
    <img src="architecture.png" alt="Cross-silo opportunity engine end-to-end architecture diagram">
    <figcaption>Four-stage architecture this run followed - see <a href="architecture.md">architecture.md</a> for the full design.</figcaption>
  </figure>

  <section id="summary">
    <h2>Run summary</h2>
    <p class="section-note">Counts from the CSVs in data/processed/, produced by the most recent pipeline run.</p>
    {render_summary_section(stats)}
  </section>

  <section class="card opportunities-card">
    <h2>Ranked opportunities</h2>
    <p class="section-note">Every field, unrestricted - the full admin-equivalent view, in the pipeline's own rank order.</p>
    {opportunities_table_html}
  </section>

  <section class="card governance-card" id="governance">
    <h2>Governance in action: financing vs. broker</h2>
    <p class="section-note">
      Same {stats['opportunity_total']} opportunities, same rank order, run through
      <code>governance.get_opportunities_for_role()</code> for two different roles. Shared columns
      (grey) are visible to both; the green columns are financing-only and the rust columns are
      broker-only - each role's line-of-business detail is invisible to the other, while entity
      identity, confidence, and the rule outcome stay visible to both. Source record IDs travel
      with every row regardless of role.
    </p>
    {governance_table_html}
  </section>

  <footer>cross-silo-opportunity-engine · generated by scripts/generate_report.py</footer>

</div>
</body>
</html>
"""


def main() -> None:
    stats = build_summary_stats()
    opportunities = governance.load_opportunities(PROCESSED_DIR / "opportunities.csv")
    financing_view = governance.get_opportunities_for_role(opportunities, Role.FINANCING)
    broker_view = governance.get_opportunities_for_role(opportunities, Role.BROKER)

    opportunities_table_html = render_opportunities_table(read_csv_rows(PROCESSED_DIR / "opportunities.csv"))
    governance_table_html = render_governance_comparison(opportunities, financing_view, broker_view)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_page(stats, opportunities_table_html, governance_table_html), encoding="utf-8")
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
