"""Tests for `training.build_ll84_index`.

Exercises both the real-LL84 path (BBL + address columns present) and the
synthetic fallback (the committed `dataset.csv` shape, no address columns).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from training.build_ll84_index import (
    build_ll84_index,
    normalize_address,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "sample_ll84.csv"

EXPECTED_COLUMNS = [
    "bbl",
    "address_raw",
    "address_normalized",
    "property_type",
    "borough",
    "gross_floor_area_sqft",
    "year_built",
    "number_of_buildings",
    "site_eui",
]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("123 Main Street", "123 MAIN ST"),
        ("  123   main   street  ", "123 MAIN ST"),
        ("742 Evergreen Terrace", "742 EVERGREEN TER"),
        ("1600 Pennsylvania Avenue, NW", "1600 PENNSYLVANIA AVE NW"),
        ("North 7th St.", "N 7TH ST"),
        ("West 145th Street", "W 145TH ST"),
        ("Park Boulevard", "PARK BLVD"),
        ("Ocean Pkwy", "OCEAN PKWY"),
        ("", ""),
        (None, ""),
    ],
)
def test_normalize_address_rules(raw: object, expected: str) -> None:
    assert normalize_address(raw) == expected


def test_normalize_address_handles_nan() -> None:
    assert normalize_address(float("nan")) == ""


def test_synthetic_fallback_columns_in_order() -> None:
    raw = pd.read_csv(FIXTURE, dtype=str)
    out = build_ll84_index(raw)
    assert list(out.columns) == EXPECTED_COLUMNS


def test_synthetic_fallback_drops_invalid_rows() -> None:
    raw = pd.read_csv(FIXTURE, dtype=str)
    out = build_ll84_index(raw)
    # Fixture has rows that should drop: EUI=Not Available, EUI=0.5, EUI=1500,
    # missing GFA, missing year_built, "Jersey City" (non-NYC).
    assert len(out) >= 5
    assert set(out["borough"].unique()).issubset(
        {"manhattan", "brooklyn", "queens", "bronx", "staten-island"}
    )


def test_synthetic_fallback_bbls_are_ten_digit_strings() -> None:
    raw = pd.read_csv(FIXTURE, dtype=str)
    out = build_ll84_index(raw)
    assert (out["bbl"].str.len() == 10).all()
    assert out["bbl"].str.isdigit().all()
    assert out["bbl"].is_unique


def test_synthetic_fallback_addresses_are_normalized() -> None:
    raw = pd.read_csv(FIXTURE, dtype=str)
    out = build_ll84_index(raw)
    for addr in out["address_normalized"]:
        assert addr == addr.upper()
        assert "  " not in addr


def test_real_ll84_columns_are_used_when_present() -> None:
    raw = pd.DataFrame(
        {
            "BBL - 10 digits": ["1000010001", "3001230045"],
            "Address 1 (self-reported)": ["123 Main Street", "456 Park Avenue"],
            "Largest Property Use Type": ["Office", "Multifamily Housing"],
            "Borough": ["Manhattan", "Brooklyn"],
            "Largest Property Use Type - Gross Floor Area (ft²)": ["120000", "45000"],
            "Year Built": ["1980", "1925"],
            "Number of Buildings": ["1", "1"],
            "Site EUI (kBtu/ft²)": ["65.0", "87.3"],
        }
    )
    out = build_ll84_index(raw)
    assert list(out["bbl"]) == ["1000010001", "3001230045"]
    assert list(out["address_raw"]) == ["123 Main Street", "456 Park Avenue"]
    assert list(out["address_normalized"]) == ["123 MAIN ST", "456 PARK AVE"]
    assert list(out["property_type"]) == ["office", "multifamily-housing"]
    assert list(out["borough"]) == ["manhattan", "brooklyn"]


def test_malformed_bbl_falls_back_to_synthetic() -> None:
    raw = pd.DataFrame(
        {
            "BBL - 10 digits": ["abc", "1234567890"],
            "Address 1": ["1 First St", "2 Second St"],
            "Largest Property Use Type": ["Office", "Office"],
            "Borough": ["Manhattan", "Manhattan"],
            "Largest Property Use Type - Gross Floor Area (ft²)": ["50000", "50000"],
            "Year Built": ["1980", "1980"],
            "Number of Buildings": ["1", "1"],
            "Site EUI (kBtu/ft²)": ["65.0", "65.0"],
        }
    )
    out = build_ll84_index(raw)
    bbls = sorted(out["bbl"].tolist())
    assert "1234567890" in bbls
    other = next(b for b in bbls if b != "1234567890")
    assert other.startswith("1")
    assert len(other) == 10


def test_eui_outside_band_is_dropped_when_eui_present() -> None:
    raw = pd.DataFrame(
        {
            "Largest Property Use Type": ["Office"] * 4,
            "Borough": ["Manhattan"] * 4,
            "Largest Property Use Type - Gross Floor Area (ft²)": ["50000"] * 4,
            "Year Built": ["1980"] * 4,
            "Number of Buildings": ["1"] * 4,
            "Site EUI (kBtu/ft²)": ["0.5", "1.0", "1000.0", "1500.0"],
        }
    )
    out = build_ll84_index(raw)
    assert sorted(out["site_eui"].tolist()) == [1.0, 1000.0]


def test_unknown_property_type_dropped() -> None:
    raw = pd.DataFrame(
        {
            "Largest Property Use Type": ["Bowling Alley", "Office"],
            "Borough": ["Manhattan", "Manhattan"],
            "Largest Property Use Type - Gross Floor Area (ft²)": ["50000", "50000"],
            "Year Built": ["1980", "1980"],
            "Number of Buildings": ["1", "1"],
            "Site EUI (kBtu/ft²)": ["65.0", "65.0"],
        }
    )
    out = build_ll84_index(raw)
    assert list(out["property_type"]) == ["office"]


def test_non_nyc_borough_dropped() -> None:
    raw = pd.DataFrame(
        {
            "Largest Property Use Type": ["Office", "Office"],
            "Borough": ["Jersey City", "Manhattan"],
            "Largest Property Use Type - Gross Floor Area (ft²)": ["50000", "50000"],
            "Year Built": ["1980", "1980"],
            "Number of Buildings": ["1", "1"],
            "Site EUI (kBtu/ft²)": ["65.0", "65.0"],
        }
    )
    out = build_ll84_index(raw)
    assert list(out["borough"]) == ["manhattan"]


def test_missing_required_columns_raises() -> None:
    raw = pd.DataFrame({"Borough": ["Manhattan"]})
    with pytest.raises(KeyError):
        build_ll84_index(raw)


def test_missing_eui_column_yields_nan() -> None:
    raw = pd.DataFrame(
        {
            "Largest Property Use Type": ["Office"],
            "Borough": ["Manhattan"],
            "Largest Property Use Type - Gross Floor Area (ft²)": ["50000"],
            "Year Built": ["1980"],
            "Number of Buildings": ["1"],
        }
    )
    out = build_ll84_index(raw)
    assert len(out) == 1
    assert pd.isna(out["site_eui"].iat[0])


def test_rows_sorted_by_bbl_then_address() -> None:
    raw = pd.read_csv(FIXTURE, dtype=str)
    out = build_ll84_index(raw)
    keys = list(zip(out["bbl"], out["address_normalized"], strict=True))
    assert keys == sorted(keys)


def test_is_deterministic() -> None:
    raw = pd.read_csv(FIXTURE, dtype=str)
    a = build_ll84_index(raw)
    b = build_ll84_index(raw)
    pd.testing.assert_frame_equal(a, b)


def test_parquet_roundtrip_is_byte_identical(tmp_path: Path) -> None:
    raw = pd.read_csv(FIXTURE, dtype=str)
    out = build_ll84_index(raw)
    path_a = tmp_path / "a.parquet"
    path_b = tmp_path / "b.parquet"
    out.to_parquet(path_a, engine="pyarrow", compression="snappy", index=False)
    out.to_parquet(path_b, engine="pyarrow", compression="snappy", index=False)
    assert path_a.read_bytes() == path_b.read_bytes()
    pd.testing.assert_frame_equal(pd.read_parquet(path_a), out)
