"""Tests for `training.build_peer_cohorts`.

Reuses `tests/fixtures/sample_ll84.csv` (the same pinned fixture used by
`test_clean.py`) so the cohort builder is exercised on a known-shape input
without standing up the synthetic-dataset script.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from training.build_peer_cohorts import (
    AGE_BANDS,
    assign_age_band,
    build_peer_cohorts,
)
from training.clean import load_and_clean

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "sample_ll84.csv"

EXPECTED_COLUMNS = [
    "property_type",
    "borough",
    "age_band",
    "cohort_size",
    "p25",
    "median",
    "p75",
    "eui_sorted",
]


@pytest.fixture
def cohorts() -> pd.DataFrame:
    return build_peer_cohorts(load_and_clean(FIXTURE))


def test_returns_documented_columns_in_order(cohorts: pd.DataFrame) -> None:
    assert list(cohorts.columns) == EXPECTED_COLUMNS


def test_age_bands_constant_lists_four_canonical_slugs() -> None:
    assert AGE_BANDS == ("pre-1950", "1950-1979", "1980-1999", "2000-plus")


@pytest.mark.parametrize(
    ("year", "expected"),
    [
        (1900, "pre-1950"),
        (1949, "pre-1950"),
        (1950, "1950-1979"),
        (1979, "1950-1979"),
        (1980, "1980-1999"),
        (1999, "1980-1999"),
        (2000, "2000-plus"),
        (2024, "2000-plus"),
    ],
)
def test_assign_age_band_boundaries(year: int, expected: str) -> None:
    assert assign_age_band(year) == expected


def test_age_band_values_are_canonical(cohorts: pd.DataFrame) -> None:
    assert set(cohorts["age_band"].unique()) <= set(AGE_BANDS)


def test_one_row_per_cohort(cohorts: pd.DataFrame) -> None:
    assert not cohorts.duplicated(subset=["property_type", "borough", "age_band"]).any()


def test_rows_are_sorted_for_determinism(cohorts: pd.DataFrame) -> None:
    keys = list(zip(cohorts["property_type"], cohorts["borough"], cohorts["age_band"], strict=True))
    assert keys == sorted(keys)


def test_cohort_size_matches_eui_array_length(cohorts: pd.DataFrame) -> None:
    for _, row in cohorts.iterrows():
        assert row["cohort_size"] == len(row["eui_sorted"])


def test_eui_sorted_is_ascending(cohorts: pd.DataFrame) -> None:
    for _, row in cohorts.iterrows():
        eui = list(row["eui_sorted"])
        assert eui == sorted(eui)


def test_percentiles_match_numpy_on_sorted_array(cohorts: pd.DataFrame) -> None:
    for _, row in cohorts.iterrows():
        eui = np.asarray(row["eui_sorted"], dtype=float)
        assert row["p25"] == pytest.approx(float(np.percentile(eui, 25, method="linear")))
        assert row["median"] == pytest.approx(float(np.percentile(eui, 50, method="linear")))
        assert row["p75"] == pytest.approx(float(np.percentile(eui, 75, method="linear")))


def test_singleton_cohort_has_collapsed_percentiles() -> None:
    df = pd.DataFrame(
        {
            "property_type": ["office"],
            "borough": ["manhattan"],
            "year_built": [1985],
            "site_eui": [42.5],
        }
    )
    out = build_peer_cohorts(df)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["age_band"] == "1980-1999"
    assert row["cohort_size"] == 1
    assert row["p25"] == 42.5
    assert row["median"] == 42.5
    assert row["p75"] == 42.5
    assert row["eui_sorted"] == [42.5]


def test_known_cohort_values() -> None:
    df = pd.DataFrame(
        {
            "property_type": ["office"] * 5,
            "borough": ["manhattan"] * 5,
            "year_built": [1990, 1991, 1992, 1993, 1994],
            "site_eui": [10.0, 20.0, 30.0, 40.0, 50.0],
        }
    )
    out = build_peer_cohorts(df)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["cohort_size"] == 5
    assert row["p25"] == pytest.approx(20.0)
    assert row["median"] == pytest.approx(30.0)
    assert row["p75"] == pytest.approx(40.0)
    assert row["eui_sorted"] == [10.0, 20.0, 30.0, 40.0, 50.0]


def test_is_deterministic() -> None:
    df = load_and_clean(FIXTURE)
    a = build_peer_cohorts(df)
    b = build_peer_cohorts(df)
    pd.testing.assert_frame_equal(a, b)


def test_parquet_roundtrip_is_byte_identical(tmp_path: Path) -> None:
    df = build_peer_cohorts(load_and_clean(FIXTURE))
    path_a = tmp_path / "a.parquet"
    path_b = tmp_path / "b.parquet"
    df.to_parquet(path_a, engine="pyarrow", compression="snappy", index=False)
    df.to_parquet(path_b, engine="pyarrow", compression="snappy", index=False)
    assert path_a.read_bytes() == path_b.read_bytes()
    pd.testing.assert_frame_equal(pd.read_parquet(path_a), df)
