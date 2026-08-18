from cross_silo_opportunity_engine.ingestion.normalization import (
    normalize_address,
    normalize_entity_name,
    normalize_state,
    split_combined_address,
)


def test_normalize_address_extracts_suite():
    assert normalize_address("2200 Airport Rd, Suite 5") == {
        "address_line1": "2200 Airport Road",
        "address_line2": "Suite 5",
    }


def test_normalize_address_extracts_inline_floor_abbreviation():
    assert normalize_address("900 Congress Ave Fl 12") == {
        "address_line1": "900 Congress Avenue",
        "address_line2": "Floor 12",
    }


def test_normalize_address_extracts_ordinal_floor():
    assert normalize_address("900 Congress Avenue, 12th Floor") == {
        "address_line1": "900 Congress Avenue",
        "address_line2": "Floor 12",
    }


def test_normalize_address_no_unit():
    assert normalize_address("112 Elm Street") == {"address_line1": "112 Elm Street", "address_line2": None}


def test_normalize_address_expands_suffix_abbreviation():
    assert normalize_address("410 Westheimer Rd")["address_line1"] == "410 Westheimer Road"


def test_normalize_address_does_not_false_positive_on_ste_inside_a_word():
    # "Westheimer" contains no "Ste" token, but this guards the word-boundary regex more
    # generally: a plain street name should never be mistaken for a suite marker.
    result = normalize_address("410 Westheimer Road")
    assert result["address_line2"] is None
    assert result["address_line1"] == "410 Westheimer Road"


def test_normalize_address_empty_input():
    assert normalize_address("") == {"address_line1": None, "address_line2": None}
    assert normalize_address(None) == {"address_line1": None, "address_line2": None}


def test_split_combined_address_matches_separate_fields_normalization():
    # The debt source's single combined string should normalize to the same street line and
    # unit as the sales source's separate address column, for the same real address.
    combined = split_combined_address("900 Congress Avenue, 12th Floor, Austin, TX 78701")
    separate = normalize_address("900 Congress Ave Fl 12")
    assert combined["address_line1"] == separate["address_line1"]
    assert combined["address_line2"] == separate["address_line2"]
    assert combined["city"] == "Austin"
    assert combined["state"] == "TX"
    assert combined["postal_code"] == "78701"


def test_split_combined_address_full_state_name():
    result = split_combined_address("55 Bay Street, Boston, Massachusetts 02110")
    assert result["state"] == "MA"
    assert result["city"] == "Boston"


def test_split_combined_address_missing_zip_returns_all_none():
    assert split_combined_address("no zip code in this string") == {
        "address_line1": None,
        "address_line2": None,
        "city": None,
        "state": None,
        "postal_code": None,
    }


def test_split_combined_address_empty_input():
    assert split_combined_address("")["address_line1"] is None


def test_normalize_entity_name_strips_legal_suffix_variants():
    assert normalize_entity_name("Ashford Commercial Grp") == "Ashford Commercial Group"
    assert normalize_entity_name("Cornerstone Retail Fnd") == "Cornerstone Retail Fund"
    assert normalize_entity_name("Crestpoint Industrial Ptrs") == "Crestpoint Industrial Partners"


def test_normalize_entity_name_collapses_whitespace_and_case():
    assert normalize_entity_name("HARBORVIEW  HOLDINGS") == "Harborview Holdings"
    assert normalize_entity_name("redwood multifamily group") == "Redwood Multifamily Group"


def test_normalize_entity_name_strips_trailing_punctuation():
    assert normalize_entity_name("Harborview Holdings, Inc") == "Harborview Holdings Inc"


def test_normalize_entity_name_empty_input():
    assert normalize_entity_name("") == ""
    assert normalize_entity_name(None) == ""


def test_normalize_state_two_letter_uppercases():
    assert normalize_state("mo") == "MO"


def test_normalize_state_full_name_lookup():
    assert normalize_state("Texas") == "TX"


def test_normalize_state_unknown_title_cases():
    assert normalize_state("atlantis") == "Atlantis"


def test_normalize_state_empty_is_none():
    assert normalize_state("") is None
