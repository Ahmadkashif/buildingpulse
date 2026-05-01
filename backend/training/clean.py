"""Cleaner for the NYC LL84 disclosure CSV.

`load_and_clean(csv_path)` returns a tidy DataFrame with the six columns
documented in MVP_PLAN.md Phase 3:

    property_type, borough, gross_floor_area_sqft,
    year_built, number_of_buildings, site_eui

Standardization rules (explicit, no silent magic):

1. Source columns are read by exact NYC LL84 header names listed in
   `_SOURCE_COLUMNS`. Missing required columns raise `KeyError`.
2. Numeric columns are parsed with `pd.to_numeric(..., errors="coerce")`.
   Sentinel values "Not Available", "See Primary BBL", and blanks become NaN.
3. Rows with NaN in any required numeric column are dropped.
4. `site_eui` is filtered to `1.0 <= site_eui <= 1000.0`. Outside that
   range is treated as a data error (per CLAUDE.md modeling decision).
5. `property_type` is lowercased, stripped, then mapped through
   `_PROPERTY_TYPE_MAP`. Unmapped types are dropped.
6. `borough` is lowercased, stripped, internal whitespace collapsed to
   one hyphen. Values not in `_BOROUGHS` are dropped.
7. The result is reset to a clean RangeIndex so the function is pure
   (deterministic on input — no row ordering surprises from upstream).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

__all__ = ["load_and_clean"]


_SOURCE_COLUMNS: dict[str, str] = {
    "Largest Property Use Type": "property_type",
    "Borough": "borough",
    "Largest Property Use Type - Gross Floor Area (ft²)": "gross_floor_area_sqft",
    "Year Built": "year_built",
    "Number of Buildings": "number_of_buildings",
    "Site EUI (kBtu/ft²)": "site_eui",
}

_NUMERIC_COLUMNS: tuple[str, ...] = (
    "gross_floor_area_sqft",
    "year_built",
    "number_of_buildings",
    "site_eui",
)

# LL84 raw label (lowercased + stripped) → canonical PropertyType literal.
# Keep this map narrow on purpose: anything not listed is dropped, which
# keeps Phase 3 honest about what the baseline model is trained on.
_PROPERTY_TYPE_MAP: dict[str, str] = {
    "multifamily housing": "multifamily-housing",
    "office": "office",
    "hotel": "hotel",
    "retail store": "retail",
    "retail": "retail",
    "enclosed mall": "retail",
    "strip mall": "retail",
    "hospital (general medical & surgical)": "hospital",
    "hospital": "hospital",
    "mixed use property": "mixed-use",
    "mixed-use property": "mixed-use",
    "mixed use": "mixed-use",
    "mixed-use": "mixed-use",
}

_BOROUGHS: frozenset[str] = frozenset({"manhattan", "brooklyn", "queens", "bronx", "staten-island"})

_OUTPUT_COLUMNS: list[str] = [
    "property_type",
    "borough",
    "gross_floor_area_sqft",
    "year_built",
    "number_of_buildings",
    "site_eui",
]

_EUI_MIN: float = 1.0
_EUI_MAX: float = 1000.0


def _normalize_borough(value: str) -> str:
    return "-".join(value.strip().lower().split())


def load_and_clean(csv_path: str | Path) -> pd.DataFrame:
    """Load the LL84 CSV and return a tidy DataFrame.

    Pure: same input file → same output frame, every time.
    """
    raw = pd.read_csv(csv_path, dtype=str, low_memory=False)

    missing = [c for c in _SOURCE_COLUMNS if c not in raw.columns]
    if missing:
        raise KeyError(f"missing required LL84 columns: {missing}")

    df = raw[list(_SOURCE_COLUMNS)].rename(columns=_SOURCE_COLUMNS).copy()

    for col in _NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=list(_NUMERIC_COLUMNS))

    df = df[(df["site_eui"] >= _EUI_MIN) & (df["site_eui"] <= _EUI_MAX)]

    df["property_type"] = (
        df["property_type"].astype(str).str.strip().str.lower().map(_PROPERTY_TYPE_MAP)
    )
    df = df.dropna(subset=["property_type"])

    df["borough"] = df["borough"].astype(str).map(_normalize_borough)
    df = df[df["borough"].isin(_BOROUGHS)]

    df["year_built"] = df["year_built"].astype(int)
    df["number_of_buildings"] = df["number_of_buildings"].astype(int)
    df["gross_floor_area_sqft"] = df["gross_floor_area_sqft"].astype(int)

    df = df[_OUTPUT_COLUMNS].reset_index(drop=True)
    return df
