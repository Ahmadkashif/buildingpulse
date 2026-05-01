"""Process-wide registry for the LL84 address-lookup parquet artifact.

Loads ``ll84_index.parquet`` once at app startup; subsequent reads return
the cached :class:`~app.domain.address.types.Ll84Index`. Construction is
the load — a missing file raises immediately so the FastAPI lifespan hook
fails fast rather than letting the first ``/api/address/lookup`` request
blow up.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from app.domain.address.types import Ll84Index, Ll84Record

_INDEX_FILE = "ll84_index.parquet"


def _to_record(row: pd.Series) -> Ll84Record:
    eui_raw = row["site_eui"]
    site_eui: float | None
    if eui_raw is None or (isinstance(eui_raw, float) and math.isnan(eui_raw)):
        site_eui = None
    else:
        site_eui = float(eui_raw)
    return Ll84Record(
        bbl=str(row["bbl"]),
        address_raw=str(row["address_raw"]),
        address_normalized=str(row["address_normalized"]),
        property_type=str(row["property_type"]),
        borough=str(row["borough"]),
        gross_floor_area_sqft=int(row["gross_floor_area_sqft"]),
        year_built=int(row["year_built"]),
        number_of_buildings=int(row["number_of_buildings"]),
        site_eui=site_eui,
    )


class Ll84IndexRegistry:
    """Holds the loaded LL84 address lookup index."""

    def __init__(self, artifacts_dir: Path | str) -> None:
        directory = Path(artifacts_dir)
        index_path = directory / _INDEX_FILE
        if not index_path.is_file():
            raise FileNotFoundError(f"missing LL84 index artifact: {index_path}")
        df = pd.read_parquet(index_path, engine="pyarrow")
        records = tuple(_to_record(row) for _, row in df.iterrows())
        self._index = Ll84Index(records=records)

    @property
    def index(self) -> Ll84Index:
        return self._index


__all__ = ["Ll84IndexRegistry"]
