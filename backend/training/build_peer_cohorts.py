"""Build the peer-cohort lookup table from the LL84 disclosure CSV.

CLI entry point: ``python -m training.build_peer_cohorts``.

Reads ``backend/data/dataset.csv``, cleans via :func:`training.clean.load_and_clean`,
buckets each row into an age band, groups by ``(property_type, borough, age_band)``,
and writes one parquet artifact under ``backend/artifacts/peer_cohorts.parquet``:

Each output row contains:

* ``property_type``    — canonical literal from the cleaner.
* ``borough``          — canonical borough slug from the cleaner.
* ``age_band``         — one of ``pre-1950``, ``1950-1979``, ``1980-1999``, ``2000-plus``.
* ``cohort_size``      — number of buildings in the cohort.
* ``p25``, ``median``, ``p75`` — linear-interpolation percentiles of ``site_eui``.
* ``eui_sorted``       — full sorted ``site_eui`` array for exact percentile lookup.

The output is deterministic given the input CSV: rows are sorted by
``(property_type, borough, age_band)``, ``eui_sorted`` is ascending, and the
parquet is written with a fixed compression scheme. Re-running on the same
input file produces an output whose contents are byte-identical when read back.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from training.clean import load_and_clean

__all__ = ["AGE_BANDS", "assign_age_band", "build_peer_cohorts", "main"]

_BACKEND_ROOT: Path = Path(__file__).resolve().parents[1]
_DATA_PATH: Path = _BACKEND_ROOT / "data" / "dataset.csv"
_ARTIFACTS_DIR: Path = _BACKEND_ROOT / "artifacts"
_COHORTS_PATH: Path = _ARTIFACTS_DIR / "peer_cohorts.parquet"

AGE_BANDS: tuple[str, ...] = ("pre-1950", "1950-1979", "1980-1999", "2000-plus")

_OUTPUT_COLUMNS: list[str] = [
    "property_type",
    "borough",
    "age_band",
    "cohort_size",
    "p25",
    "median",
    "p75",
    "eui_sorted",
]


def assign_age_band(year_built: int) -> str:
    """Return the canonical age-band slug for a given construction year."""
    if year_built < 1950:
        return "pre-1950"
    if year_built < 1980:
        return "1950-1979"
    if year_built < 2000:
        return "1980-1999"
    return "2000-plus"


def build_peer_cohorts(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate a cleaned LL84 frame into one row per peer cohort.

    Pure: same input frame → same output frame, every time. The output
    is sorted by ``(property_type, borough, age_band)`` and each
    ``eui_sorted`` array is ascending.
    """
    working = df[["property_type", "borough", "year_built", "site_eui"]].copy()
    working["age_band"] = working["year_built"].map(assign_age_band)

    rows: list[dict[str, object]] = []
    grouped = working.groupby(["property_type", "borough", "age_band"], sort=True)
    for (property_type, borough, age_band), group in grouped:
        eui = np.sort(group["site_eui"].to_numpy(dtype=float))
        rows.append(
            {
                "property_type": property_type,
                "borough": borough,
                "age_band": age_band,
                "cohort_size": int(eui.size),
                "p25": float(np.percentile(eui, 25, method="linear")),
                "median": float(np.percentile(eui, 50, method="linear")),
                "p75": float(np.percentile(eui, 75, method="linear")),
                "eui_sorted": eui.tolist(),
            }
        )

    out = pd.DataFrame(rows, columns=_OUTPUT_COLUMNS)
    out = out.sort_values(["property_type", "borough", "age_band"], kind="mergesort").reset_index(
        drop=True
    )
    return out


def main() -> None:
    df = load_and_clean(_DATA_PATH)
    cohorts = build_peer_cohorts(df)
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    cohorts.to_parquet(_COHORTS_PATH, engine="pyarrow", compression="snappy", index=False)


if __name__ == "__main__":
    main()
