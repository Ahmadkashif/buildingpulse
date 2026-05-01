"""GET /api/sponsor and GET /api/sponsor/cta — controller.

`GET /api/sponsor` returns the active sponsor's five public display
fields (id, name, logoUrl, ctaLabel, ctaUrl). Lead-routing fields
(email, webhook) are intentionally never serialized here — they stay
server-side.

`GET /api/sponsor/cta` records a ``SponsorCtaFollowed`` audit row for
the given ``prediction_id`` (required) and optional ``scenario_id``,
then 302s to the configured sponsor CTA URL with both ids and the
``utm_source=buildingpulse`` / ``utm_campaign=ll97_report`` campaign
tags appended.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.deps import (
    get_audit_service,
    get_request_id,
    get_sponsor_service,
    get_trace_id,
)
from app.domain.audit import SponsorCtaFollowed
from app.services.resource.audit.service import AuditService
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
        self.router.add_api_route(
            "/sponsor/cta",
            self.cta,
            methods=["GET", "HEAD"],
            status_code=status.HTTP_302_FOUND,
            response_class=RedirectResponse,
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

    async def cta(
        self,
        sponsor_service: Annotated[
            SponsorResourceService, Depends(get_sponsor_service)
        ],
        audit: Annotated[AuditService, Depends(get_audit_service)],
        prediction_id: Annotated[str, Query(min_length=1)],
        scenario_id: Annotated[str | None, Query(min_length=1)] = None,
    ) -> RedirectResponse:
        await audit.record(
            SponsorCtaFollowed(
                occurred_at=datetime.now(UTC),
                request_id=get_request_id(),
                trace_id=get_trace_id(),
                actor_session_id="",
                prediction_id=prediction_id,
                scenario_id=scenario_id,
            )
        )
        url = sponsor_service.cta_redirect_url(prediction_id, scenario_id)
        return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


router = SponsorController().router

__all__ = [
    "SponsorController",
    "SponsorPublic",
    "SponsorResponseEnvelope",
    "router",
]
