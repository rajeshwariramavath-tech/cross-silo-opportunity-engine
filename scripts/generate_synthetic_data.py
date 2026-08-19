"""Generates data/raw/sales_records.csv and data/raw/debt_records.csv: 400 deliberately messy
rows each, spread across 15 zip codes, with a controlled mix of match difficulty so entity
resolution (and zip-code blocking specifically) has something real to work with:

- ~130 "shared" entities: same real address in both files, different formatting/casing/legal
  suffix on each side - the clear-match case.
- ~20 "ambiguous" entities: same company, same zip, but a different street address in each
  file (a second property) - same zip block, but address/name signals disagree, so these
  should land in the review queue rather than auto-matching or auto-rejecting.
- ~250 entities each that only appear in one file - most of these coincidentally share a zip
  with something on the other side (with 15 zips and ~650 entities, that's unavoidable), which
  is exactly the "same block, not a match" case blocking has to still score correctly rather
  than assume away.

Reproducible via a fixed random seed - rerun this script and you get the same data back.
"""

from __future__ import annotations

import csv
import itertools
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
N_SHARED = 130
N_AMBIGUOUS = 20
N_SALES_ONLY = 247
N_DEBT_ONLY = 247

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"

ZIP_POOL = [
    ("43215", "Columbus", "OH", "Ohio"),
    ("80202", "Denver", "CO", "Colorado"),
    ("78701", "Austin", "TX", "Texas"),
    ("02110", "Boston", "MA", "Massachusetts"),
    ("38118", "Memphis", "TN", "Tennessee"),
    ("60601", "Chicago", "IL", "Illinois"),
    ("30303", "Atlanta", "GA", "Georgia"),
    ("37217", "Nashville", "TN", "Tennessee"),
    ("70130", "New Orleans", "LA", "Louisiana"),
    ("77006", "Houston", "TX", "Texas"),
    ("98101", "Seattle", "WA", "Washington"),
    ("94117", "San Francisco", "CA", "California"),
    ("97201", "Portland", "OR", "Oregon"),
    ("33131", "Miami", "FL", "Florida"),
    ("85018", "Phoenix", "AZ", "Arizona"),
]

STREET_NAMES = [
    "Main", "Elm", "Oak", "Riverside", "Congress", "Market", "Union", "Bay", "Canal", "Peachtree",
    "Airport", "Westheimer", "Camelback", "Fillmore", "Grant", "Tryon", "Yale", "Tampa", "Bannock",
    "Independent", "Lakeshore", "Franklin", "Jefferson", "Washington", "Highland", "Sunset",
    "Broadway", "Commerce", "Industrial", "Harbor", "Meridian", "Century", "Liberty", "Heritage", "Summit",
]
STREET_TYPES = [("St", "Street"), ("Ave", "Avenue"), ("Blvd", "Boulevard"), ("Dr", "Drive"), ("Rd", "Road"), ("Ln", "Lane"), ("Pkwy", "Parkway")]

NAME_PREFIXES = [
    "Meridian", "Oakwood", "Silverline", "Harborview", "Crestpoint", "Bluepeak", "Ashford", "Northgate",
    "Delta Ridge", "Cornerstone", "Pinnacle", "Redwood", "Vantage Point", "Summit Bay", "Ironwood", "Cascade",
    "Larkspur", "Brightline", "Foundry Square", "Golden Gate", "Maple Crest", "Sable Point", "Twin Rivers",
    "Highland Park", "Copperfield", "Willowbrook", "Bayshore", "Stonebridge", "Ember Ridge", "Marlin Bay",
    "Falcon Creek", "Union Pacific", "Grayson", "Prairie Wind", "Coastal Bend", "Ridgeline", "Amberleaf",
    "Steelyard", "Hollow Creek", "Palmetto Coast", "Timberlake", "Quarrystone", "Windermere", "Blackthorn",
    "Sagebrush", "Copper Basin", "Ferngate", "Ashgrove", "Birchwood", "Canyon Point", "Driftwood",
    "Elm Hollow", "Fairview", "Greystone", "Hearthstone", "Ironbridge", "Juniper Bend", "Kestrel",
    "Lakeshore", "Millbrook", "Nightingale", "Overlook", "Pinecrest", "Quailridge", "Rosewood",
    "Silverpine", "Thornfield", "Underhill", "Valley Forge", "Westbrook", "Yellowpine", "Zenith Point",
]
NAME_SUFFIXES = [
    "Retail", "Industrial", "Office", "Capital", "Realty", "Holdings", "Ventures", "Partners",
    "Group", "Trust", "Fund", "Investors", "Properties", "Development", "Logistics", "Residential", "Commercial",
]
LEGAL_SUFFIXES = ["LLC", "Inc", "Inc.", "Grp", "Ptrs", "Fnd", "LP"]

PROPERTY_TYPES = ["Office", "Retail", "Industrial", "Multifamily", "Land"]
LOAN_TYPES = ["Term Loan", "Bridge Loan", "Refinance", "Construction Loan"]
BROKER_NAMES = ["J. Alvarez", "Maria Chen", "Priya Nair", "Derek Wu", "S. Whitfield", "Nathan Ford",
                "Elena Ruiz", "Tom O'Neill", "K. Bennett", "Alicia Fox", "R. Delgado", "Wendy Park"]
LENDER_NAMES = ["Republic Trust Bank", "Highline Lending", "First Capital Bank", "Gulf Coast Bank",
                "Pacific Northwest Trust", "Delta Commercial Credit", "Lakefront Bank", "Piedmont Capital",
                "Volunteer State Bank", "Crescent City Lending", "Golden State Credit Union", "Front Range Bank",
                "Gateway Commercial Bank", "Hoosier Capital Bank", "Midlands Trust", "Sandia Federal Bank",
                "Capitol Lakes Bank", "Great Lakes Commercial Bank", "Piedmont Triad Bank", "Lowcountry Bank",
                "Sierra Nevada Bank", "Desert Southwest Bank", "Empire State Trust"]


def make_entity_names(rng: random.Random, count: int) -> list[str]:
    combos = [f"{prefix} {suffix}" for prefix, suffix in itertools.product(NAME_PREFIXES, NAME_SUFFIXES)]
    rng.shuffle(combos)
    return combos[:count]


def make_address(rng: random.Random) -> dict:
    zip_code, city, state, state_full = rng.choice(ZIP_POOL)
    return {
        "street_number": rng.randint(10, 9899),
        "street_name": rng.choice(STREET_NAMES),
        "street_type": rng.choice(STREET_TYPES),
        "zip": zip_code, "city": city, "state": state, "state_full": state_full,
    }


def render_street(address: dict, rng: random.Random, with_unit: bool | None = None) -> tuple[str, str | None]:
    abbrev, full = address["street_type"]
    street_type = abbrev if rng.random() < 0.5 else full
    street = f"{address['street_number']} {address['street_name']} {street_type}"
    if with_unit is None:
        with_unit = rng.random() < 0.3
    unit = None
    if with_unit:
        style = rng.choice(["suite", "ste", "floor_short", "floor_ordinal"])
        n = rng.randint(1, 40)
        if style == "suite":
            unit = f"Suite {n}"
        elif style == "ste":
            unit = f"Ste {n}"
        elif style == "floor_short":
            unit = f"Fl {n}"
        else:
            suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            unit = f"{n}{suffix} Floor"
    return street, unit


def render_name(base_name: str, side: str, rng: random.Random) -> str:
    suffix_prob = 0.75 if side == "debt" else 0.25
    name = base_name
    if rng.random() < suffix_prob:
        name = f"{name} {rng.choice(LEGAL_SUFFIXES)}"

    style = rng.choices(["normal", "upper", "lower", "double_space"], weights=[60, 15, 15, 10])[0]
    if style == "upper":
        name = name.upper()
    elif style == "lower":
        name = name.lower()
    elif style == "double_space":
        words = name.split(" ")
        if len(words) > 1:
            idx = rng.randrange(len(words) - 1)
            words[idx] = words[idx] + " "
        name = " ".join(words)
    return name


def render_date(d: date, rng: random.Random) -> str:
    style = rng.choice(["mdy", "iso", "long", "dmon"])
    if style == "mdy":
        return d.strftime("%m/%d/%Y")
    if style == "iso":
        return d.strftime("%Y-%m-%d")
    if style == "long":
        return f"{d.strftime('%B')} {d.day}, {d.year}"  # avoids the non-portable %-d strftime flag
    return d.strftime("%d-%b-%y")


def render_currency(amount: int, rng: random.Random) -> str:
    return f"${amount:,}" if rng.random() < 0.5 else str(amount)


def random_date(rng: random.Random, start: date, end: date) -> date:
    span = (end - start).days
    return start + timedelta(days=rng.randint(0, span))


def blank_one_required_field(row: dict, required_fields: list[str], rng: random.Random) -> None:
    row[rng.choice(required_fields)] = ""


def build_entities(rng: random.Random) -> list[dict]:
    total = N_SHARED + N_AMBIGUOUS + N_SALES_ONLY + N_DEBT_ONLY
    names = make_entity_names(rng, total)
    entities = []
    categories = (
        ["shared"] * N_SHARED
        + ["ambiguous"] * N_AMBIGUOUS
        + ["sales_only"] * N_SALES_ONLY
        + ["debt_only"] * N_DEBT_ONLY
    )
    rng.shuffle(categories)
    for name, category in zip(names, categories):
        entity = {"name": name, "category": category, "sales_address": make_address(rng)}
        if category == "shared":
            entity["debt_address"] = entity["sales_address"]
        elif category == "ambiguous":
            same_zip_address = make_address(rng)
            same_zip_address["zip"], same_zip_address["city"], same_zip_address["state"], same_zip_address["state_full"] = (
                entity["sales_address"]["zip"], entity["sales_address"]["city"],
                entity["sales_address"]["state"], entity["sales_address"]["state_full"],
            )
            entity["debt_address"] = same_zip_address
        elif category == "debt_only":
            entity["debt_address"] = make_address(rng)
        entities.append(entity)
    return entities


def build_sales_rows(entities: list[dict], rng: random.Random) -> list[dict]:
    rows = []
    deal_id = 1001
    for entity in entities:
        if entity["category"] not in ("shared", "ambiguous", "sales_only"):
            continue
        address = entity["sales_address"]
        street, unit = render_street(address, rng)
        full_address = f"{street}, {unit}" if unit else street
        close_date = random_date(rng, date(2024, 1, 1), date(2024, 12, 31))
        zip_code = address["zip"] + (f"-{rng.randint(1000, 9999)}" if rng.random() < 0.08 else "")

        row = {
            "deal_id": f"SR-{deal_id}",
            "client_name": render_name(entity["name"], "sales", rng),
            "property_address": full_address,
            "city": address["city"] if rng.random() > 0.05 else address["city"].lower(),
            "state": address["state"] if rng.random() > 0.1 else address["state"].lower(),
            "zip": zip_code,
            "sale_price": render_currency(rng.randrange(800_000, 15_000_000, 50_000), rng),
            "close_date": render_date(close_date, rng),
            "broker_name": rng.choice(BROKER_NAMES) if rng.random() > 0.08 else "",
            "property_type": rng.choice(PROPERTY_TYPES),
        }
        if rng.random() < 0.035:
            blank_one_required_field(row, ["client_name", "property_address", "sale_price", "close_date"], rng)
        rows.append(row)
        deal_id += 1

    duplicates = rng.sample(rows, k=max(1, len(rows) // 100))
    for dup in duplicates:
        deal_id += 1
        rows.append({**dup, "deal_id": f"SR-{deal_id}"})

    return rows


def build_debt_rows(entities: list[dict], rng: random.Random) -> list[dict]:
    rows = []
    loan_num = 1
    for entity in entities:
        if entity["category"] not in ("shared", "ambiguous", "debt_only"):
            continue
        address = entity["debt_address"]
        street, unit = render_street(address, rng)
        street_and_unit = f"{street}, {unit}" if unit else street

        state_token = address["state_full"] if rng.random() < 0.15 else address["state"]
        comma_before_zip = rng.random() < 0.6
        space_after_city_comma = rng.random() < 0.85
        city_sep = ", " if space_after_city_comma else ","
        state_zip = f"{state_token}, {address['zip']}" if comma_before_zip else f"{state_token} {address['zip']}"
        combined_address = f"{street_and_unit}{city_sep}{address['city']}, {state_zip}"

        orig = random_date(rng, date(2024, 1, 1), date(2024, 12, 31))
        maturity = random_date(rng, date(2025, 6, 1), date(2032, 6, 1))
        year_prefix = "2024" if rng.random() > 0.1 else "2023"

        row = {
            "loan_ref": f"DBT-{year_prefix}-{loan_num:03d}",
            "borrower_name": render_name(entity["name"], "debt", rng),
            "property_addr": combined_address,
            "loan_amount": render_currency(rng.randrange(500_000, 10_000_000, 50_000), rng),
            "orig_date": render_date(orig, rng),
            "maturity_date": maturity.isoformat(),
            "lender_name": rng.choice(LENDER_NAMES),
            "loan_type": rng.choice(LOAN_TYPES),
            "notes": f"past due {rng.randint(15, 90)} days" if rng.random() < 0.06 else "",
        }
        if rng.random() < 0.035:
            blank_one_required_field(row, ["borrower_name", "property_addr", "loan_amount", "orig_date"], rng)
        rows.append(row)
        loan_num += 1

    duplicates = rng.sample(rows, k=max(1, len(rows) // 100))
    for dup in duplicates:
        loan_num += 1
        rows.append({**dup, "loan_ref": f"DBT-2024-{loan_num:03d}"})

    return rows


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rng = random.Random(SEED)
    entities = build_entities(rng)

    sales_rows = build_sales_rows(entities, rng)
    debt_rows = build_debt_rows(entities, rng)

    write_csv(
        RAW_DIR / "sales_records.csv", sales_rows,
        ["deal_id", "client_name", "property_address", "city", "state", "zip", "sale_price", "close_date", "broker_name", "property_type"],
    )
    write_csv(
        RAW_DIR / "debt_records.csv", debt_rows,
        ["loan_ref", "borrower_name", "property_addr", "loan_amount", "orig_date", "maturity_date", "lender_name", "loan_type", "notes"],
    )

    zip_counts: dict[str, int] = {}
    for entity in entities:
        zip_counts[entity["sales_address"]["zip"]] = zip_counts.get(entity["sales_address"]["zip"], 0) + 1

    print(f"sales_records.csv: {len(sales_rows)} rows")
    print(f"debt_records.csv: {len(debt_rows)} rows")
    print(f"entities: {len(entities)} (shared={N_SHARED}, ambiguous={N_AMBIGUOUS}, sales_only={N_SALES_ONLY}, debt_only={N_DEBT_ONLY})")
    print(f"zip codes used: {len(zip_counts)}")
    for zip_code, count in sorted(zip_counts.items()):
        print(f"  {zip_code}: {count} entities")


if __name__ == "__main__":
    main()
