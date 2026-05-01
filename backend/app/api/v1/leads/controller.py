"""POST /api/leads — controller.

Validates the lead-capture request, returns 404 when the
``prediction_id`` references no prior ``prediction_generated`` audit row,
hands off to :class:`LeadCaptureUseCaseService`, and shapes the result.

Status codes follow the idempotency contract from prd.md: a fresh
capture returns 201; a within-window re-submission returns 200 with the
same lead id.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.deps import (
    get_app_config,
    get_audit_service,
    get_lead_capture_use_case,
    get_request_id,
    get_trace_id,
)
from app.schemas import CreateLeadInput, LeadCreated
from app.services.resource.audit.service import AuditService
from app.services.usecase.lead_capture.service import (
    LeadCaptureRequest,
    LeadCaptureUseCaseService,
)


class LeadResponseEnvelope(BaseModel):
    data: LeadCreated


class LeadsController:
    """Owns the `/api/leads` router."""

    def __init__(self) -> None:
        self.router = APIRouter()
        self.router.add_api_route(
            "/leads",
            self.create,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            response_model=LeadResponseEnvelope,
            response_model_by_alias=True,
        )

    async def create(
        self,
        body: CreateLeadInput,
        response: Response,
        audit: Annotated[AuditService, Depends(get_audit_service)],
        use_case: Annotated[LeadCaptureUseCaseService, Depends(get_lead_capture_use_case)],
    ) -> dict[str, LeadCreated]:
        if not audit.prediction_exists(body.prediction_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"unknown prediction_id: {body.prediction_id}",
            )

        config = get_app_config()
        now = datetime.now(UTC)
        request = LeadCaptureRequest(
            prediction_id=body.prediction_id,
            name=body.name,
            email=body.email,
            phone=body.phone,
            role=body.role,
            sponsor_id=config.sponsor.id,
            scenario_id=body.scenario_id,
            consent_given_at=now,
            fine_snapshot_usd=body.projected_fine_usd,
            property_type=body.property_type,
            gross_floor_area_sqft=body.gross_floor_area_sqft,
            year_built=body.year_built,
            borough=body.borough,
            predicted_eui=body.predicted_eui,
            projected_fine_usd=body.projected_fine_usd,
            at_risk=body.at_risk,
            report_url=body.report_url,
            request_id=get_request_id(),
            trace_id=get_trace_id(),
            actor_session_id="",
        )

        result = await use_case.capture(request)

        response.status_code = status.HTTP_201_CREATED if result.fire else status.HTTP_200_OK
        return {"data": LeadCreated(id=result.lead.id)}


router = LeadsController().router

__all__ = ["LeadResponseEnvelope", "LeadsController", "router"]
