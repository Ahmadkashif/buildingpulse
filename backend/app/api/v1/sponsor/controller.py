"""GET /api/sponsor — controller.

Returns the active sponsor's five public display fields (id, name,
logoUrl, ctaLabel, ctaUrl). Lead-routing fields (email, webhook) are
intentionally never serialized here — they stay server-side.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.deps import get_sponsor_service
from app.services.resource.sponsor.service import SponsorResourceService


class SponsorPublic(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    logo_url: str = Field(min_length=1)
    cta_label: str = Field(min_length=1)
    cta_url: str = Field(min_length=1)


class SponsorResponseEnvelope(BaseModel):
    data: SponsorPublic


class SponsorController:
    """Owns the `/api/sponsor` router."""

    def __init__(self) -> None:
        self.router = APIRouter()
        self.router.add_api_route(
            "/sponsor",
            self.get,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            response_model=SponsorResponseEnvelope,
            response_model_by_alias=True,
        )

    async def get(
        self,
        sponsor_service: Annotated[
            SponsorResourceService, Depends(get_sponsor_service)
        ],
    ) -> dict[str, SponsorPublic]:
        display = sponsor_service.get_display()
        return {
            "data": SponsorPublic(
                id=display.id,
                name=display.name,
                logo_url=display.logo_url,
                cta_label=display.cta_label,
                cta_url=display.cta_url,
            )
        }


router = SponsorController().router

__all__ = [
    "SponsorController",
    "SponsorPublic",
    "SponsorResponseEnvelope",
    "router",
]
