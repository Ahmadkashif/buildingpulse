"""GET /api/address/lookup — controller.

Resolves a free-form NYC street address against the LL84 disclosure
index and returns the matched building record (high or low confidence)
or a 404 miss.

Gated behind the ``ADDRESS_LOOKUP_ENABLED`` env flag. When the flag is
unset or false, the endpoint returns 404 unconditionally — the address
resolver is a Phase-2 surface area and the rest of the app must boot
without it being exposed to clients.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.deps import address_lookup_enabled, get_address_service
from app.domain.address import Ll84Match
from app.services.resource.address.service import AddressResourceService


class AddressMatchPublic(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    bbl: str = Field(min_length=1)
    address_raw: str = Field(min_length=1)
    address_normalized: str = Field(min_length=1)
    property_type: str = Field(min_length=1)
    borough: str = Field(min_length=1)
    gross_floor_area_sqft: int = Field(ge=0)
    year_built: int = Field(ge=0)
    number_of_buildings: int = Field(ge=0)
    site_eui: float | None = None
    confidence: str = Field(min_length=1)


class AddressLookupResponseEnvelope(BaseModel):
    data: AddressMatchPublic


class AddressController:
    """Owns the `/api/address/lookup` router."""

    def __init__(self) -> None:
        self.router = APIRouter()
        self.router.add_api_route(
            "/address/lookup",
            self.lookup,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            response_model=AddressLookupResponseEnvelope,
            response_model_by_alias=True,
        )

    async def lookup(
        self,
        address_service: Annotated[AddressResourceService, Depends(get_address_service)],
        address: Annotated[str | None, Query()] = None,
    ) -> dict[str, AddressMatchPublic]:
        if not address_lookup_enabled():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        if address is None or not address.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="address query parameter is required",
            )
        result = address_service.lookup(address)
        if not isinstance(result, Ll84Match):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        record = result.record
        return {
            "data": AddressMatchPublic(
                bbl=record.bbl,
                address_raw=record.address_raw,
                address_normalized=record.address_normalized,
                property_type=record.property_type,
                borough=record.borough,
                gross_floor_area_sqft=record.gross_floor_area_sqft,
                year_built=record.year_built,
                number_of_buildings=record.number_of_buildings,
                site_eui=record.site_eui,
                confidence=result.confidence,
            )
        }


router = AddressController().router

__all__ = [
    "AddressController",
    "AddressLookupResponseEnvelope",
    "AddressMatchPublic",
    "router",
]
