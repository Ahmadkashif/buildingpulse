"""Unit tests for ``app.domain.address.resolver``.

Targets: 100% branch coverage and ≥90% mutation kill rate. The fixture
index is small and pinned inline so reviewers can read the test file
top-to-bottom and see exactly which records each behavior is asserting
against.
"""

from __future__ import annotations

import pytest
from app.domain.address import (
    AMBIGUITY_MARGIN,
    FUZZY_CUTOFF,
    Ll84Index,
    Ll84Match,
    Ll84Miss,
    Ll84Record,
    lookup,
    normalize_address,
)


def _record(
    *,
    bbl: str,
    address_raw: str,
    address_normalized: str | None = None,
    site_eui: float | None = 80.0,
) -> Ll84Record:
    return Ll84Record(
        bbl=bbl,
        address_raw=address_raw,
        address_normalized=(
            address_normalized if address_normalized is not None else normalize_address(address_raw)
        ),
        property_type="office",
        borough="manhattan",
        gross_floor_area_sqft=50000,
        year_built=1980,
        number_of_buildings=1,
        site_eui=site_eui,
    )


@pytest.fixture
def index() -> Ll84Index:
    return Ll84Index(
        records=(
            _record(bbl="1000010001", address_raw="350 5th Avenue"),
            _record(bbl="1000020002", address_raw="1 World Trade Center"),
            _record(bbl="1000030003", address_raw="200 West 57th Street"),
            _record(bbl="1000040004", address_raw="789 Madison Avenue"),
            _record(bbl="1000050005", address_raw="789 Park Avenue"),
        )
    )


# --- normalize_address ----------------------------------------------


def test_normalize_uppercases_and_strips_punctuation() -> None:
    assert normalize_address("350 5th Avenue") == "350 5TH AVE"


def test_normalize_canonicalizes_suffix_variants() -> None:
    assert normalize_address("123 Main Street") == normalize_address("123 main st")


def test_normalize_canonicalizes_directions() -> None:
    assert normalize_address("200 West 57th Street") == "200 W 57TH ST"


def test_normalize_collapses_internal_whitespace() -> None:
    assert normalize_address("  350    5th   Ave  ") == "350 5TH AVE"


def test_normalize_returns_empty_for_punctuation_only_input() -> None:
    assert normalize_address("---,,,") == ""


# --- lookup: malformed input ----------------------------------------


def test_lookup_rejects_non_string_input(index: Ll84Index) -> None:
    result = lookup(None, index)  # type: ignore[arg-type]

    assert isinstance(result, Ll84Miss)
    assert result.reason == "malformed"


def test_lookup_rejects_integer_input(index: Ll84Index) -> None:
    result = lookup(12345, index)  # type: ignore[arg-type]

    assert isinstance(result, Ll84Miss)
    assert result.reason == "malformed"


def test_lookup_rejects_empty_string(index: Ll84Index) -> None:
    result = lookup("", index)

    assert isinstance(result, Ll84Miss)
    assert result.reason == "malformed"


def test_lookup_rejects_whitespace_only_string(index: Ll84Index) -> None:
    result = lookup("   \t  ", index)

    assert isinstance(result, Ll84Miss)
    assert result.reason == "malformed"


def test_lookup_rejects_punctuation_only_string(index: Ll84Index) -> None:
    result = lookup(".,;:!", index)

    assert isinstance(result, Ll84Miss)
    assert result.reason == "malformed"


# --- lookup: empty index --------------------------------------------


def test_lookup_against_empty_index_returns_not_found() -> None:
    empty = Ll84Index(records=())

    result = lookup("350 5th Avenue", empty)

    assert isinstance(result, Ll84Miss)
    assert result.reason == "not_found"


# --- lookup: exact hits ---------------------------------------------


def test_lookup_exact_hit_returns_high_confidence_match(index: Ll84Index) -> None:
    result = lookup("350 5th Avenue", index)

    assert isinstance(result, Ll84Match)
    assert result.confidence == "high"
    assert result.record.bbl == "1000010001"


def test_lookup_exact_hit_normalizes_input(index: Ll84Index) -> None:
    # "Avenue" → "AVE", different casing — still hits the same record.
    result = lookup("350 5TH ave", index)

    assert isinstance(result, Ll84Match)
    assert result.confidence == "high"
    assert result.record.bbl == "1000010001"


def test_lookup_multiple_exact_matches_returns_low_confidence() -> None:
    # Two records with identical normalized addresses — caller cannot
    # disambiguate without more input.
    dup_index = Ll84Index(
        records=(
            _record(bbl="A", address_raw="100 Main St"),
            _record(bbl="B", address_raw="100 Main Street"),  # same normalized form
        )
    )

    result = lookup("100 Main Street", dup_index)

    assert isinstance(result, Ll84Match)
    assert result.confidence == "low"
    # First match in iteration order wins.
    assert result.record.bbl == "A"


# --- lookup: fuzzy hits ---------------------------------------------


def test_lookup_fuzzy_typo_returns_match(index: Ll84Index) -> None:
    # Typo: "Avenu" instead of "Avenue".
    result = lookup("350 5th Avenu", index)

    assert isinstance(result, Ll84Match)
    assert result.record.bbl == "1000010001"


def test_lookup_fuzzy_unique_top_candidate_is_high_confidence(index: Ll84Index) -> None:
    # "1 World Trade Center" has no near-rival in the index → should be
    # confidently high-confidence even with a typo.
    result = lookup("1 World Trade Centr", index)

    assert isinstance(result, Ll84Match)
    assert result.confidence == "high"
    assert result.record.bbl == "1000020002"


def test_lookup_clear_winner_among_multiple_fuzzy_is_high_confidence() -> None:
    # Both candidates clear the cutoff, but the top has a clearly higher
    # ratio than the runner-up — the resolver should be confident.
    # Records use explicit address_normalized so the test pins the exact
    # strings the fuzzy matcher sees.
    clear_index = Ll84Index(
        records=(
            _record(
                bbl="WIN",
                address_raw="100 Main St Win",
                address_normalized="100 MAIN ST WIN",
            ),
            _record(
                bbl="WST",
                address_raw="100 Main St West",
                address_normalized="100 MAIN ST WEST",
            ),
        )
    )

    result = lookup("100 Main St Wing", clear_index)

    assert isinstance(result, Ll84Match)
    assert result.confidence == "high"
    assert result.record.bbl == "WIN"


def test_lookup_ambiguous_fuzzy_returns_low_confidence() -> None:
    # Query "123 Broadway" can plausibly mean either "123 Broadway St"
    # or "123 Broadway Ave" — both within the FUZZY_CUTOFF and within
    # the AMBIGUITY_MARGIN of each other. The resolver should flag the
    # caller that it cannot disambiguate.
    ambiguous_index = Ll84Index(
        records=(
            _record(bbl="ST", address_raw="123 Broadway Street"),
            _record(bbl="AV", address_raw="123 Broadway Avenue"),
        )
    )

    result = lookup("123 Broadway", ambiguous_index)

    assert isinstance(result, Ll84Match)
    assert result.confidence == "low"


# --- lookup: misses --------------------------------------------------


def test_lookup_no_close_match_returns_not_found(index: Ll84Index) -> None:
    result = lookup("99999 Nowhere Lane", index)

    assert isinstance(result, Ll84Miss)
    assert result.reason == "not_found"


# --- module-level constants -----------------------------------------


def test_fuzzy_cutoff_is_a_ratio() -> None:
    assert 0.0 < FUZZY_CUTOFF < 1.0


def test_ambiguity_margin_is_small_positive() -> None:
    assert 0.0 < AMBIGUITY_MARGIN < 0.5
