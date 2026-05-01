"""Pure peer-cohort lookup with broad-fallback rule.

Given a building's ``(property_type, borough, year_built)`` and a
predicted EUI, find the cohort that should be used to score it. The
narrow cohort is ``(property_type, borough, age_band)``. If that cohort
has fewer than ``MIN_COHORT_SIZE`` rows, the lookup falls back, in
order:

1. drop ``borough`` → ``(property_type, age_band)``,
2. drop ``age_band`` → ``(property_type)``.

The function takes the loaded cohorts frame as a dependency and never
performs I/O. Each input cohort row carries an ``eui_sorted`` ascending
array; broadened cohorts merge those arrays.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.domain.peer.types import PeerCohort, PeerOutlook

__all__ = ["AGE_BANDS", "MIN_COHORT_SIZE", "assign_age_band", "lookup"]

MIN_COHORT_SIZE: int = 30

AGE_BANDS: tuple[str, ...] = ("pre-1950", "1950-1979", "1980-1999", "2000-plus")


def assign_age_band(year_built: int) -> str:
    """Return the canonical age-band slug for a given construction year."""
    if year_built < 1950:
        return "pre-1950"
    if year_built < 1980:
        return "1950-1979"
    if year_built < 2000:
        return "1980-1999"
    return "2000-plus"


def _merge_sorted(rows: pd.DataFrame) -> np.ndarray:
    """Concatenate the per-row ``eui_sorted`` arrays into one ascending array."""
    arrays = [np.asarray(values, dtype=float) for values in rows["eui_sorted"]]
    merged = np.concatenate(arrays)
    merged.sort()
    return merged


def lookup(
    *,
    cohorts: pd.DataFrame,
    property_type: str,
    borough: str,
    year_built: int,
    predicted_eui: float,
) -> PeerOutlook:
    """Return the peer outlook for a single building.

    Falls back from the narrow ``(property_type, borough, age_band)``
    cohort to ``(property_type, age_band)`` and finally ``(property_type)``
    whenever the running cohort size is below ``MIN_COHORT_SIZE``.
    """
    age_band = assign_age_band(year_built)

    same_type = cohorts[cohorts["property_type"] == property_type]

    narrow = same_type[
        (same_type["borough"] == borough) & (same_type["age_band"] == age_band)
    ]
    if int(narrow["cohort_size"].sum()) >= MIN_COHORT_SIZE:
        eui_sorted = _merge_sorted(narrow)
        cohort = PeerCohort(
            property_type=property_type, borough=borough, age_band=age_band
        )
    else:
        mid = same_type[same_type["age_band"] == age_band]
        if int(mid["cohort_size"].sum()) >= MIN_COHORT_SIZE:
            eui_sorted = _merge_sorted(mid)
            cohort = PeerCohort(
                property_type=property_type, borough=None, age_band=age_band
            )
        else:
            eui_sorted = _merge_sorted(same_type)
            cohort = PeerCohort(property_type=property_type, borough=None, age_band=None)

    size = int(eui_sorted.size)
    p25 = float(np.percentile(eui_sorted, 25, method="linear"))
    median = float(np.percentile(eui_sorted, 50, method="linear"))
    p75 = float(np.percentile(eui_sorted, 75, method="linear"))

    rank = int(np.searchsorted(eui_sorted, float(predicted_eui), side="right"))
    percentile = int(round(rank * 100 / size))

    return PeerOutlook(
        cohort=cohort,
        cohort_size=size,
        median=median,
        p25=p25,
        p75=p75,
        percentile=percentile,
    )
