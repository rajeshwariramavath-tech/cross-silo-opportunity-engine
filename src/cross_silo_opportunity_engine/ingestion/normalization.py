"""Address and entity-name normalization applied before records enter entity resolution."""

from __future__ import annotations

import re

# Suite/Unit must be followed by whitespace, a period, or end-of-string so this doesn't
# fire inside an ordinary word that happens to start with "Ste" (e.g. "Westheimer").
_UNIT_PATTERN = re.compile(r",?\s*\b(?:Suite|Ste\.?|Unit)(?=[\s.]|$)\s*#?\s*([\w-]+)", re.IGNORECASE)
_ORDINAL_FLOOR_PATTERN = re.compile(r",?\s*\b(\d+)(?:st|nd|rd|th)\s+Floor\b", re.IGNORECASE)
_FLOOR_PATTERN = re.compile(r",?\s*\bFl(?:oor)?\.?(?=[\s.]|$)\s*#?\s*([\w-]+)", re.IGNORECASE)

_STREET_SUFFIX_EXPANSIONS = {
    "st": "Street",
    "ave": "Avenue",
    "blvd": "Boulevard",
    "dr": "Drive",
    "rd": "Road",
    "ln": "Lane",
    "pkwy": "Parkway",
    "hwy": "Highway",
}

_NAME_TOKEN_REPLACEMENTS = {
    "llc": "LLC",
    "inc": "Inc",
    "incorporated": "Inc",
    "lp": "LP",
    "llp": "LLP",
    "reit": "REIT",
    "grp": "Group",
    "ptrs": "Partners",
    "fnd": "Fund",
}

_STATE_ABBREVIATIONS = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
    "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
    "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
    "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
    "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
}


def normalize_address(raw_address: str) -> dict[str, str | None]:
    """Extracts a suite/floor unit into address_line2 and expands the street's suffix abbreviation."""
    if not raw_address or not raw_address.strip():
        return {"address_line1": None, "address_line2": None}

    text = " ".join(raw_address.strip().split())
    unit: str | None = None

    match = _UNIT_PATTERN.search(text)
    if match:
        unit = f"Suite {match.group(1)}"
        text = (text[: match.start()] + text[match.end():]).strip(" ,")
    else:
        match = _ORDINAL_FLOOR_PATTERN.search(text)
        if match:
            unit = f"Floor {match.group(1)}"
            text = (text[: match.start()] + text[match.end():]).strip(" ,")
        else:
            match = _FLOOR_PATTERN.search(text)
            if match:
                unit = f"Floor {match.group(1)}"
                text = (text[: match.start()] + text[match.end():]).strip(" ,")

    words = " ".join(text.split()).split(" ")
    if words and words[-1]:
        suffix_key = words[-1].rstrip(".").lower()
        if suffix_key in _STREET_SUFFIX_EXPANSIONS:
            words[-1] = _STREET_SUFFIX_EXPANSIONS[suffix_key]
    address_line1 = " ".join(w for w in words if w) or None

    return {"address_line1": address_line1, "address_line2": unit}


def split_combined_address(raw_address: str) -> dict[str, str | None]:
    """Splits a single "street[, unit], city, state zip" string into canonical components.

    The debt source stores one combined address string per record, unlike the sales
    source's separate address/city/state/zip columns - this is the "different address
    format between systems" problem the architecture doc calls out for stage 1 to solve.
    """
    empty: dict[str, str | None] = {
        "address_line1": None, "address_line2": None,
        "city": None, "state": None, "postal_code": None,
    }
    if not raw_address or not raw_address.strip():
        return empty

    text = raw_address.strip()

    zip_match = re.search(r"(\d{5}(?:-\d{4})?)\s*$", text)
    if not zip_match:
        return empty
    postal_code = zip_match.group(1)
    remainder = text[: zip_match.start()].strip(" ,")

    state_match = re.search(r"([A-Za-z]{2,})\s*$", remainder)
    if not state_match:
        return empty
    state = normalize_state(state_match.group(1))
    remainder = remainder[: state_match.start()].strip(" ,")

    parts = [part.strip() for part in remainder.split(",") if part.strip()]
    if not parts:
        return empty
    city = parts[-1]
    street_and_unit = ", ".join(parts[:-1])

    street = normalize_address(street_and_unit)
    return {
        "address_line1": street["address_line1"],
        "address_line2": street["address_line2"],
        "city": city,
        "state": state,
        "postal_code": postal_code,
    }


def normalize_state(raw_state: str) -> str | None:
    if not raw_state or not raw_state.strip():
        return None
    cleaned = raw_state.strip()
    if len(cleaned) == 2:
        return cleaned.upper()
    return _STATE_ABBREVIATIONS.get(cleaned.lower(), cleaned.title())


def normalize_entity_name(raw_name: str) -> str:
    if not raw_name or not raw_name.strip():
        return ""

    normalized_tokens: list[str] = []
    for token in " ".join(raw_name.strip().split()).split(" "):
        stripped = token.strip(".,;:")
        if not stripped:
            continue
        replacement = _NAME_TOKEN_REPLACEMENTS.get(stripped.lower())
        normalized_tokens.append(replacement or (stripped[:1].upper() + stripped[1:].lower()))
    return " ".join(normalized_tokens)
