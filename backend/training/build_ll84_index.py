"""Build an address-keyed lookup index from the NYC LL84 disclosure CSV.

CLI entry point: ``python -m training.build_ll84_index``.

Reads ``backend/data/dataset.csv`` and writes
``backend/artifacts/ll84_index.parquet`` — one row per disclosed building,
keyed for fuzzy address lookup at runtime by
:mod:`app.domain.address.resolver`.

Output columns
==============

* ``bbl``                     — 10-digit Borough/Block/Lot string.
* ``address_raw``             — verbatim street address from the source file.
* ``address_normalized``      — uppercased, punctuation-stripped, whitespace-
                                collapsed, suffix-canonicalized form suitable
                                for fuzzy joins.
* ``property_type``           — canonical literal from :mod:`training.clean`.
* ``borough``                 — canonical borough slug.
* ``gross_floor_area_sqft``   — int.
* ``year_built``              — int.
* ``number_of_buildings``     — int.
* ``site_eui``                — float when present in source, else NaN.

Determinism
===========

Rows are sorted by ``(bbl, address_normalized)`` and the parquet is written
with a fixed compression scheme. Re-running on the same input file produces
an output whose contents are byte-identical when read back.

The repository's synthetic dataset does not carry BBL or address columns
(real LL84 PII is not committed). When those columns are absent, the script
generates deterministic synthetic identifiers from the row's stable position
and borough so the artifact still round-trips through downstream code.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

__all__ = [
    "build_ll84_index",
    "main",
    "normalize_address",
]

_BACKEND_ROOT: Path = Path(__file__).resolve().parents[1]
_DATA_PATH: Path = _BACKEND_ROOT / "data" / "dataset.csv"
_ARTIFACTS_DIR: Path = _BACKEND_ROOT / "artifacts"
_INDEX_PATH: Path = _ARTIFACTS_DIR / "ll84_index.parquet"

_BBL_CANDIDATES: tuple[str, ...] = (
    "BBL - 10 digits",
    "NYC Borough, Block and Lot (BBL) self-reported",
    "NYC Borough, Block and Lot (BBL)",
    "BBL",
)

_ADDRESS_CANDIDATES: tuple[str, ...] = (
    "Address 1 (self-reported)",
    "Address 1",
    "Property Address",
    "Street Address",
    "Address",
)

_PROPERTY_TYPE_COL: str = "Largest Property Use Type"
_BOROUGH_COL: str = "Borough"
_GFA_COL: str = "Largest Property Use Type - Gross Floor Area (ft²)"
_YEAR_BUILT_COL: str = "Year Built"
_NUM_BUILDINGS_COL: str = "Number of Buildings"
_SITE_EUI_COL: str = "Site EUI (kBtu/ft²)"

_BOROUGH_TO_CODE: dict[str, str] = {
    "manhattan": "1",
    "bronx": "2",
    "brooklyn": "3",
    "queens": "4",
    "staten-island": "5",
}

# LL84 raw label (lowercased + stripped) → canonical PropertyType literal.
# Mirrors training.clean._PROPERTY_TYPE_MAP; duplicated here to avoid taking
# a private dependency on that module.
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

# USPS-ish suffix canonicalization. Run after punctuation strip + uppercase
# so the keys match the post-cleanup tokens.
_SUFFIX_MAP: dict[str, str] = {
    "STREET": "ST",
    "STR": "ST",
    "AVENUE": "AVE",
    "AV": "AVE",
    "BOULEVARD": "BLVD",
    "ROAD": "RD",
    "DRIVE": "DR",
    "PLACE": "PL",
    "COURT": "CT",
    "PARKWAY": "PKWY",
    "TERRACE": "TER",
    "LANE": "LN",
    "HIGHWAY": "HWY",
    "SQUARE": "SQ",
    "EXPRESSWAY": "EXPY",
    "NORTH": "N",
    "SOUTH": "S",
    "EAST": "E",
    "WEST": "W",
}

_PUNCT_RE: re.Pattern[str] = re.compile(r"[^\w\s]+")
_WS_RE: re.Pattern[str] = re.compile(r"\s+")

_OUTPUT_COLUMNS: list[str] = [
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


def normalize_address(value: object) -> str:
    """Return a normalized form of a free-form address string.

    Pure: same input → same output. Returns an empty string for missing
    or non-string inputs so callers can filter on truthiness.

    Rules:
    1. Cast to string, strip outer whitespace.
    2. Uppercase.
    3. Replace any run of non-alphanumeric characters with a single space.
    4. Map common street-suffix and direction tokens to their USPS forms
       (``STREET → ST``, ``AVENUE → AVE``, ``NORTH → N``, …).
    5. Collapse internal whitespace to single spaces.
    """
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text = text.upper()
    text = _PUNCT_RE.sub(" ", text)
    tokens = [_SUFFIX_MAP.get(tok, tok) for tok in text.split()]
    return _WS_RE.sub(" ", " ".join(tokens)).strip()


def _normalize_borough(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    return "-".join(str(value).strip().lower().split())


def _pick_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str | None:
    for name in candidates:
        if name in df.columns:
            return name
    return None


def _synthetic_bbl(borough: str, position: int) -> str:
    """Deterministically build a 10-digit BBL-shaped string.

    Format: ``B BBBBB LLLL`` (borough digit + 5-digit block + 4-digit lot),
    derived from the row's stable position so reruns are identical.
    """
    code = _BOROUGH_TO_CODE.get(borough, "0")
    block = position // 10000
    lot = position % 10000
    return f"{code}{block:05d}{lot:04d}"


def _synthetic_address(position: int) -> str:
    """Deterministic placeholder address string for synthetic inputs."""
    house = 100 + position
    return f"{house} SYNTH ST"


def build_ll84_index(df: pd.DataFrame) -> pd.DataFrame:
    """Convert a raw LL84-shaped DataFrame into the address lookup index.

    Pure: same input frame → same output frame, every time. Output is
    sorted by ``(bbl, address_normalized)``.

    Rows are dropped when they fail any of the cleaning rules from
    :mod:`training.clean` (unknown property type, non-NYC borough, EUI
    out of the [1, 1000] band when EUI is present, missing required
    numeric columns).
    """
    required = {
        _PROPERTY_TYPE_COL,
        _BOROUGH_COL,
        _GFA_COL,
        _YEAR_BUILT_COL,
        _NUM_BUILDINGS_COL,
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise KeyError(f"missing required LL84 columns: {missing}")

    bbl_col = _pick_column(df, _BBL_CANDIDATES)
    addr_col = _pick_column(df, _ADDRESS_CANDIDATES)
    has_eui = _SITE_EUI_COL in df.columns

    work = pd.DataFrame(index=df.index.copy())
    work["property_type"] = (
        df[_PROPERTY_TYPE_COL].astype(str).str.strip().str.lower().map(_PROPERTY_TYPE_MAP)
    )
    work["borough"] = df[_BOROUGH_COL].map(_normalize_borough)
    work["gross_floor_area_sqft"] = pd.to_numeric(df[_GFA_COL], errors="coerce")
    work["year_built"] = pd.to_numeric(df[_YEAR_BUILT_COL], errors="coerce")
    work["number_of_buildings"] = pd.to_numeric(df[_NUM_BUILDINGS_COL], errors="coerce")
    work["site_eui"] = pd.to_numeric(df[_SITE_EUI_COL], errors="coerce") if has_eui else np.nan

    if bbl_col:
        work["bbl_raw"] = df[bbl_col].astype(str).str.strip()
    else:
        work["bbl_raw"] = pd.Series([""] * len(df), index=df.index)
    work["address_raw"] = (
        df[addr_col].astype(str).str.strip()
        if addr_col
        else pd.Series([""] * len(df), index=df.index)
    )

    work = work.dropna(subset=["gross_floor_area_sqft", "year_built", "number_of_buildings"])
    work = work.dropna(subset=["property_type"])
    work = work[work["borough"].isin(_BOROUGHS)]

    if has_eui:
        eui_in_band = work["site_eui"].between(1.0, 1000.0)
        work = work[work["site_eui"].isna() | eui_in_band]

    work = work.reset_index(drop=True)

    work["gross_floor_area_sqft"] = work["gross_floor_area_sqft"].astype(int)
    work["year_built"] = work["year_built"].astype(int)
    work["number_of_buildings"] = work["number_of_buildings"].astype(int)

    if bbl_col:
        bbl_series = work["bbl_raw"].astype(str).str.replace(r"\D", "", regex=True)
        bbl_series = bbl_series.where(bbl_series.str.len() == 10, other="")
    else:
        bbl_series = pd.Series([""] * len(work), index=work.index, dtype=str)

    if addr_col:
        addr_raw_series = work["address_raw"]
    else:
        addr_raw_series = pd.Series([""] * len(work), index=work.index, dtype=str)

    bbl_out: list[str] = []
    addr_raw_out: list[str] = []
    addr_norm_out: list[str] = []
    for pos, (_, row) in enumerate(work.iterrows()):
        borough = str(row["borough"])
        bbl_value = bbl_series.iat[pos] if bbl_col else ""
        if not bbl_value:
            bbl_value = _synthetic_bbl(borough, pos)
        addr_raw_value = addr_raw_series.iat[pos] if addr_col else ""
        if not addr_raw_value:
            addr_raw_value = _synthetic_address(pos)
        bbl_out.append(bbl_value)
        addr_raw_out.append(addr_raw_value)
        addr_norm_out.append(normalize_address(addr_raw_value))

    out = pd.DataFrame(
        {
            "bbl": bbl_out,
            "address_raw": addr_raw_out,
            "address_normalized": addr_norm_out,
            "property_type": work["property_type"].astype(str).to_numpy(),
            "borough": work["borough"].astype(str).to_numpy(),
            "gross_floor_area_sqft": work["gross_floor_area_sqft"].astype(int).to_numpy(),
            "year_built": work["year_built"].astype(int).to_numpy(),
            "number_of_buildings": work["number_of_buildings"].astype(int).to_numpy(),
            "site_eui": work["site_eui"].astype(float).to_numpy(),
        },
        columns=_OUTPUT_COLUMNS,
    )

    out = out.sort_values(["bbl", "address_normalized"], kind="mergesort").reset_index(drop=True)
    return out


def main() -> None:
    raw = pd.read_csv(_DATA_PATH, dtype=str, low_memory=False)
    index = build_ll84_index(raw)
    _ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    index.to_parquet(_INDEX_PATH, engine="pyarrow", compression="snappy", index=False)


if __name__ == "__main__":
    main()
