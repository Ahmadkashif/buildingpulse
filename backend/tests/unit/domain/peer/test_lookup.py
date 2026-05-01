"""Unit tests for ``app.domain.peer.lookup``.

Targets: 100% branch coverage and ≥90% mutation kill rate. The fallback
chain (full → drop borough → drop age_band) is exercised end-to-end with
synthetic cohort frames whose sizes straddle ``MIN_COHORT_SIZE``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from app.domain.peer import (
    AGE_BANDS,
    MIN_COHORT_SIZE,
    PeerCohort,
    PeerOutlook,
    assign_age_band,
    lookup,
)


def _row(
    *,
    property_type: str,
    borough: str,
    age_band: str,
    eui: list[float],
) -> dict[str, object]:
    arr = sorted(eui)
    return {
        "property_type": property_type,
        "borough": borough,
        "age_band": age_band,
        "cohort_size": len(arr),
        "p25": float(np.percentile(arr, 25, method="linear")) if arr else 0.0,
        "median": float(np.percentile(arr, 50, method="linear")) if arr else 0.0,
        "p75": float(np.percentile(arr, 75, method="linear")) if arr else 0.0,
        "eui_sorted": arr,
    }


def _frame(rows: list[dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=[
            "property_type",
            "borough",
            "age_band",
            "cohort_size",
            "p25",
            "median",
            "p75",
            "eui_sorted",
        ],
    )


# --- assign_age_band -------------------------------------------------


def test_assign_age_band_pre_1950_lower_boundary() -> None:
    assert assign_age_band(1900) == "pre-1950"


def test_assign_age_band_pre_1950_upper_boundary() -> None:
    assert assign_age_band(1949) == "pre-1950"


def test_assign_age_band_1950_lower_boundary() -> None:
    assert assign_age_band(1950) == "1950-1979"


def test_assign_age_band_1950_upper_boundary() -> None:
    assert assign_age_band(1979) == "1950-1979"


def test_assign_age_band_1980_lower_boundary() -> None:
    assert assign_age_band(1980) == "1980-1999"


def test_assign_age_band_1980_upper_boundary() -> None:
    assert assign_age_band(1999) == "1980-1999"


def test_assign_age_band_2000_lower_boundary() -> None:
    assert assign_age_band(2000) == "2000-plus"


def test_assign_age_band_modern_year() -> None:
    assert assign_age_band(2024) == "2000-plus"


def test_age_bands_constant_lists_every_canonical_slug_in_order() -> None:
    assert AGE_BANDS == ("pre-1950", "1950-1979", "1980-1999", "2000-plus")


def test_min_cohort_size_constant_is_30() -> None:
    assert MIN_COHORT_SIZE == 30


# --- lookup: L1 narrow cohort hit ------------------------------------


def test_l1_returns_narrow_cohort_when_size_at_threshold() -> None:
    """Exactly 30 rows in the narrow cohort uses the narrow cohort."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 31)],
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="pre-1950",
                eui=[100.0] * 30,
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=15.0,
    )

    assert result.cohort == PeerCohort(
        property_type="office", borough="manhattan", age_band="pre-1950"
    )
    assert result.cohort_size == 30
    assert result.median == pytest.approx(15.5)
    assert result.p25 == pytest.approx(8.25)
    assert result.p75 == pytest.approx(22.75)


def test_l1_picks_correct_borough_partition() -> None:
    """The Bronx cohort is large but the lookup is asked about Manhattan."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 31)],
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="pre-1950",
                eui=[1000.0] * 50,
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=15.0,
    )

    assert result.cohort.borough == "manhattan"
    assert result.cohort_size == 30


def test_l1_picks_correct_property_type_partition() -> None:
    """A 'hotel' cohort is large but the lookup is asked about 'office'."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 31)],
            ),
            _row(
                property_type="hotel",
                borough="manhattan",
                age_band="pre-1950",
                eui=[1000.0] * 50,
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=15.0,
    )

    assert result.cohort.property_type == "office"
    assert result.cohort_size == 30


# --- lookup: L2 fallback (drop borough) ------------------------------


def test_l2_drops_borough_when_narrow_cohort_below_threshold() -> None:
    """Narrow cohort has 29 rows (< 30) → fall back to (property_type, age_band)."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 30)],  # 29
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="pre-1950",
                eui=[float(i) for i in range(50, 51)],  # 1 row, low value
            ),
            _row(
                property_type="office",
                borough="brooklyn",
                age_band="pre-1950",
                eui=[100.0] * 5,  # 5 rows, padding the L2 cohort to ≥ 30
            ),
            _row(
                property_type="office",
                borough="manhattan",
                age_band="2000-plus",
                eui=[999.0] * 100,  # different age_band — must be excluded
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=200.0,
    )

    assert result.cohort == PeerCohort(
        property_type="office", borough=None, age_band="pre-1950"
    )
    # 29 + 1 + 5 = 35, no rows from the 2000-plus age band leaked in.
    assert result.cohort_size == 35
    # predicted EUI of 200 is above every value in the merged cohort → 100th percentile.
    assert result.percentile == 100


def test_l2_excludes_other_age_bands_from_aggregation() -> None:
    """Even when the alternative age_band is huge, it must not enter the L2 cohort."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[1.0] * 10,
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="pre-1950",
                eui=[2.0] * 25,
            ),
            _row(
                property_type="office",
                borough="manhattan",
                age_band="1980-1999",
                eui=[1000.0] * 1000,
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=1.5,
    )

    # 10 + 25 = 35 rows, all in pre-1950
    assert result.cohort.age_band == "pre-1950"
    assert result.cohort.borough is None
    assert result.cohort_size == 35


# --- lookup: L3 fallback (drop age_band too) -------------------------


def test_l3_drops_age_band_when_l2_also_below_threshold() -> None:
    """Both narrow and L2 cohorts are < 30 → fall all the way back to property_type."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[10.0] * 5,
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="pre-1950",
                eui=[20.0] * 5,
            ),
            _row(
                property_type="office",
                borough="manhattan",
                age_band="2000-plus",
                eui=[30.0] * 25,
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=25.0,
    )

    assert result.cohort == PeerCohort(
        property_type="office", borough=None, age_band=None
    )
    # 5 + 5 + 25 = 35
    assert result.cohort_size == 35


def test_l3_uses_all_property_type_rows_regardless_of_age_band_or_borough() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[1.0] * 5,
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="2000-plus",
                eui=[100.0] * 50,
            ),
            _row(
                property_type="hotel",
                borough="manhattan",
                age_band="pre-1950",
                eui=[999.0] * 1000,
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=50.0,
    )

    assert result.cohort.property_type == "office"
    assert result.cohort.borough is None
    assert result.cohort.age_band is None
    # 5 + 50 = 55 office rows, no hotel rows
    assert result.cohort_size == 55


# --- threshold boundary ---------------------------------------------


def test_threshold_29_narrow_falls_back_to_l2() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(29)],
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="pre-1950",
                eui=[float(i) for i in range(10)],
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=10.0,
    )

    assert result.cohort.borough is None  # broadened


def test_threshold_30_at_l2_uses_l2_not_l3() -> None:
    """Exactly 30 rows at the (property_type, age_band) level fires L2, not L3."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(5)],  # 5
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="pre-1950",
                eui=[float(i) for i in range(25)],  # 25 → L2 sum is exactly 30
            ),
            _row(
                property_type="office",
                borough="manhattan",
                age_band="2000-plus",
                eui=[float(i) for i in range(50)],  # huge alternate age_band
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=10.0,
    )

    assert result.cohort.borough is None
    assert result.cohort.age_band == "pre-1950"  # not None — L2, not L3
    assert result.cohort_size == 30


def test_threshold_30_narrow_uses_l1() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(30)],
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="pre-1950",
                eui=[1000.0] * 100,
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=10.0,
    )

    assert result.cohort.borough == "manhattan"


# --- percentile semantics ------------------------------------------


def test_percentile_is_int_in_zero_to_one_hundred() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 31)],
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=15.0,
    )

    assert isinstance(result.percentile, int)
    assert 0 <= result.percentile <= 100


def test_percentile_zero_when_predicted_below_every_value() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(10, 40)],
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=0.0,
    )

    assert result.percentile == 0


def test_percentile_one_hundred_when_predicted_above_every_value() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 31)],
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=999.0,
    )

    assert result.percentile == 100


def test_percentile_uses_right_inclusive_rank() -> None:
    """Rank counts values ≤ predicted; ties push the rank up."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 31)],
            ),
        ]
    )

    # Exactly 15 values are ≤ 15 → percentile = round(15/30 * 100) = 50.
    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=15.0,
    )

    assert result.percentile == 50


def test_percentile_scales_with_predicted_value() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 31)],
            ),
        ]
    )

    low = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=5.0,
    )
    high = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=25.0,
    )

    assert low.percentile == 17  # round(5/30*100)
    assert high.percentile == 83  # round(25/30*100)


# --- aggregated stats reflect merged eui_sorted ---------------------


def test_aggregated_percentiles_use_merged_sorted_array() -> None:
    """At L2/L3, p25/median/p75 come from the concatenated cohort, not per-row stats."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 21)],  # 1..20
            ),
            _row(
                property_type="office",
                borough="bronx",
                age_band="pre-1950",
                eui=[float(i) for i in range(21, 41)],  # 21..40
            ),
        ]
    )

    # Narrow (manhattan, pre-1950) is 20 rows < 30 → L2 fires.
    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=20.0,
    )

    expected = np.arange(1, 41, dtype=float)
    assert result.cohort_size == 40
    assert result.median == pytest.approx(float(np.percentile(expected, 50)))
    assert result.p25 == pytest.approx(float(np.percentile(expected, 25)))
    assert result.p75 == pytest.approx(float(np.percentile(expected, 75)))


# --- determinism / purity ------------------------------------------


def test_lookup_is_pure_same_inputs_same_outputs() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 51)],
            ),
        ]
    )

    a = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=25.0,
    )
    b = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=25.0,
    )

    assert a == b


def test_lookup_does_not_mutate_input_frame() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 51)],
            ),
        ]
    )
    snapshot = cohorts.copy(deep=True)

    lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=25.0,
    )

    pd.testing.assert_frame_equal(cohorts, snapshot)


def test_returns_peer_outlook_dataclass() -> None:
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[float(i) for i in range(1, 31)],
            ),
        ]
    )

    result = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=15.0,
    )

    assert isinstance(result, PeerOutlook)
    assert isinstance(result.cohort, PeerCohort)


# --- year_built drives the age_band filter --------------------------


def test_year_built_controls_age_band_selection_at_l1() -> None:
    """Two narrow cohorts in the same borough, different age_bands, same size."""
    cohorts = _frame(
        [
            _row(
                property_type="office",
                borough="manhattan",
                age_band="pre-1950",
                eui=[10.0] * 30,
            ),
            _row(
                property_type="office",
                borough="manhattan",
                age_band="2000-plus",
                eui=[200.0] * 30,
            ),
        ]
    )

    pre = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=1925,
        predicted_eui=15.0,
    )
    modern = lookup(
        cohorts=cohorts,
        property_type="office",
        borough="manhattan",
        year_built=2024,
        predicted_eui=15.0,
    )

    assert pre.cohort.age_band == "pre-1950"
    assert pre.median == pytest.approx(10.0)
    assert modern.cohort.age_band == "2000-plus"
    assert modern.median == pytest.approx(200.0)
