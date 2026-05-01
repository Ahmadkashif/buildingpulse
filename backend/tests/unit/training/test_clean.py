"""Tests for `training.clean.load_and_clean`.

The fixture `tests/fixtures/sample_ll84.csv` is a tiny pinned CSV with one
row per cleaning rule the function enforces. Every branch in clean.py is
covered by reading this file once and asserting on the resulting frame.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from training.clean import load_and_clean

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "sample_ll84.csv"

EXPECTED_COLUMNS = [
    "property_type",
    "borough",
    "gross_floor_area_sqft",
    "year_built",
    "number_of_buildings",
    "site_eui",
]


@pytest.fixture
def cleaned() -> pd.DataFrame:
    return load_and_clean(FIXTURE)


def test_returns_documented_columns_in_order(cleaned: pd.DataFrame) -> None:
    assert list(cleaned.columns) == EXPECTED_COLUMNS


def test_keeps_only_canonical_rows(cleaned: pd.DataFrame) -> None:
    # 6 valid rows in the fixture; the rest violate exactly one rule each.
    assert len(cleaned) == 6


def test_drops_missing_site_eui(cleaned: pd.DataFrame) -> None:
    # The "Not Available" site_eui row (Multifamily / Brooklyn / 1930) is gone.
    assert not ((cleaned["year_built"] == 1930) & (cleaned["borough"] == "brooklyn")).any()


def test_filters_eui_out_of_range(cleaned: pd.DataFrame) -> None:
    assert (cleaned["site_eui"] >= 1.0).all()
    assert (cleaned["site_eui"] <= 1000.0).all()
    # The 0.5 and 1500.0 rows are dropped.
    assert 0.5 not in cleaned["site_eui"].to_numpy()
    assert 1500.0 not in cleaned["site_eui"].to_numpy()


def test_eui_boundaries_inclusive(tmp_path: Path) -> None:
    csv = tmp_path / "boundaries.csv"
    csv.write_text(
        "Largest Property Use Type,Borough,"
        "Largest Property Use Type - Gross Floor Area (ft²),"
        "Year Built,Number of Buildings,Site EUI (kBtu/ft²)\n"
        "Office,Manhattan,10000,2000,1,1\n"
        "Office,Manhattan,10000,2000,1,1000\n"
        "Office,Manhattan,10000,2000,1,1000.0001\n"
        "Office,Manhattan,10000,2000,1,0.9999\n"
    )
    df = load_and_clean(csv)
    assert sorted(df["site_eui"].tolist()) == [1.0, 1000.0]


def test_drops_unknown_property_type(cleaned: pd.DataFrame) -> None:
    assert "warehouse" not in cleaned["property_type"].unique()


def test_drops_unknown_borough(cleaned: pd.DataFrame) -> None:
    assert "jersey-city" not in cleaned["borough"].unique()
    assert set(cleaned["borough"].unique()) <= {
        "manhattan",
        "brooklyn",
        "queens",
        "bronx",
        "staten-island",
    }


def test_standardizes_property_type_labels(cleaned: pd.DataFrame) -> None:
    assert "hospital" in cleaned["property_type"].unique()
    assert "multifamily-housing" in cleaned["property_type"].unique()
    assert "retail" in cleaned["property_type"].unique()
    assert "mixed-use" in cleaned["property_type"].unique()
    # No raw LL84 strings leak through.
    raws = {"Multifamily Housing", "Hospital (General Medical & Surgical)", "Retail Store"}
    assert not (set(cleaned["property_type"].unique()) & raws)


def test_standardizes_borough_with_internal_whitespace(cleaned: pd.DataFrame) -> None:
    assert "staten-island" in cleaned["borough"].unique()


def test_drops_rows_missing_numeric_values(cleaned: pd.DataFrame) -> None:
    # Rows with blank GFA, "Not Available" year_built, or missing num_buildings are dropped.
    assert cleaned[EXPECTED_COLUMNS].notna().all().all()


def test_numeric_columns_are_integer_typed(cleaned: pd.DataFrame) -> None:
    assert cleaned["gross_floor_area_sqft"].dtype.kind == "i"
    assert cleaned["year_built"].dtype.kind == "i"
    assert cleaned["number_of_buildings"].dtype.kind == "i"
    assert cleaned["site_eui"].dtype.kind == "f"


def test_result_has_clean_range_index(cleaned: pd.DataFrame) -> None:
    assert list(cleaned.index) == list(range(len(cleaned)))


def test_is_deterministic() -> None:
    a = load_and_clean(FIXTURE)
    b = load_and_clean(FIXTURE)
    pd.testing.assert_frame_equal(a, b)


def test_missing_required_column_raises(tmp_path: Path) -> None:
    csv = tmp_path / "bad.csv"
    csv.write_text("Borough,Year Built\nManhattan,1990\n")
    with pytest.raises(KeyError, match="missing required LL84 columns"):
        load_and_clean(csv)
