"""API boundary schemas (Pydantic).

Symbols are kept here while `requests.py` and `responses.py` are split out
in a later phase. Tests and controllers import from `app.schemas` directly.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

PropertyType = Literal[
    "multifamily-housing",
    "office",
    "hotel",
    "retail",
    "hospital",
    "mixed-use",
]

Borough = Literal[
    "manhattan",
    "brooklyn",
    "queens",
    "bronx",
    "staten-island",
]

AgeBand = Literal["pre-1950", "1950-1979", "1980-1999", "2000-plus"]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=False,
        extra="forbid",
        protected_namespaces=(),
    )


class CreateBuildingInput(ApiModel):
    property_type: PropertyType
    borough: Borough
    gross_floor_area_sqft: int = Field(ge=500, le=5_000_000, strict=True)
    year_built: int = Field(ge=1800, le=2026, strict=True)
    number_of_buildings: int = Field(ge=1, le=10, strict=True)


class Prediction(ApiModel):
    site_eui_kbtu_per_sqft: float
    interval_low: float
    interval_high: float
    model_version: str = Field(min_length=1)


class PeerCohort(ApiModel):
    property_type: PropertyType
    borough: Borough | None
    age_band: AgeBand | None


class Peer(ApiModel):
    cohort: PeerCohort
    cohort_size: int = Field(ge=0)
    median_site_eui: float
    p25_site_eui: float
    p75_site_eui: float
    percentile: int = Field(ge=0, le=100)


class FineYear(ApiModel):
    year: int = Field(ge=2024, le=2034, strict=True)
    projected_annual_fine_usd: float


class LL97(ApiModel):
    cap_kbtu_per_sqft_2024_to_2029: float
    cap_kbtu_per_sqft_2030_to_2034: float
    projected_annual_fine_usd_2024: float
    projected_annual_fine_usd_2030: float
    at_risk: bool = Field(strict=True)
    fine_series: list[FineYear] = Field(min_length=1)


class PredictionResponse(ApiModel):
    id: str = Field(min_length=1)
    generated_at: datetime
    input: CreateBuildingInput
    prediction: Prediction
    peer: Peer
    ll97: LL97


__all__ = [
    "LL97",
    "AgeBand",
    "ApiModel",
    "Borough",
    "CreateBuildingInput",
    "FineYear",
    "Peer",
    "PeerCohort",
    "Prediction",
    "PredictionResponse",
    "PropertyType",
]
