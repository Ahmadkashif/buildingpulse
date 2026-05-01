"""POST /api/predictions — controller.

Calls the real prediction resource service to produce the `prediction`
block (point estimate + interval + model version), the `peer` block
(percentile, p25/median/p75, cohort echo), and the `ll97` block
(period caps, period fines, year-by-year ``fineSeries``, and ``atRisk``
verdict). The controller records a ``PredictionGenerated`` audit event
tagged with the same `request_id` that appears on the request's
structured log line.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.deps import (
    get_audit_service,
    get_prediction_service,
    get_request_id,
    get_trace_id,
)
from app.domain.audit.types import PredictionGenerated
from app.schemas import CreateBuildingInput, PredictionResponse
from app.services.resource.audit.service import AuditService
from app.services.resource.prediction.service import PredictionResourceService


class PredictionResponseEnvelope(BaseModel):
    data: PredictionResponse


class PredictionsController:
    """Owns the `/api/predictions` router."""

    def __init__(self) -> None:
        self.router = APIRouter()
        self.router.add_api_route(
            "/predictions",
            self.create,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
            response_model=PredictionResponseEnvelope,
            response_model_by_alias=True,
        )

    async def create(
        self,
        body: CreateBuildingInput,
        audit: Annotated[AuditService, Depends(get_audit_service)],
        prediction_service: Annotated[PredictionResourceService, Depends(get_prediction_service)],
    ) -> dict[str, Any]:
        prediction_id = f"pred_{uuid4().hex}"
        generated_at = datetime.now(UTC)

        result = prediction_service.predict(
            property_type=body.property_type,
            borough=body.borough,
            gross_floor_area_sqft=body.gross_floor_area_sqft,
            year_built=body.year_built,
            number_of_buildings=body.number_of_buildings,
        )
        eui = result.eui
        peer = result.peer
        ll97 = result.ll97

        payload: dict[str, Any] = {
            "id": prediction_id,
            "generatedAt": generated_at.isoformat(),
            "input": body.model_dump(by_alias=True),
            "prediction": {
                "siteEuiKbtuPerSqft": eui.value,
                "intervalLow": eui.low,
                "intervalHigh": eui.high,
                "modelVersion": eui.model_version,
            },
            "peer": {
                "cohort": {
                    "propertyType": peer.cohort.property_type,
                    "borough": peer.cohort.borough,
                    "ageBand": peer.cohort.age_band,
                },
                "cohortSize": peer.cohort_size,
                "medianSiteEui": peer.median,
                "p25SiteEui": peer.p25,
                "p75SiteEui": peer.p75,
                "percentile": peer.percentile,
            },
            "ll97": {
                "capKbtuPerSqft2024To2029": ll97.cap_current,
                "capKbtuPerSqft2030To2034": ll97.cap_future,
                "projectedAnnualFineUsd2024": ll97.fine_current,
                "projectedAnnualFineUsd2030": ll97.fine_future,
                "atRisk": ll97.at_risk,
                "fineSeries": [
                    {
                        "year": row.year,
                        "projectedAnnualFineUsd": row.projected_annual_fine_usd,
                    }
                    for row in ll97.fine_series
                ],
            },
        }

        await audit.record(
            PredictionGenerated(
                occurred_at=generated_at,
                request_id=get_request_id(),
                trace_id=get_trace_id(),
                actor_session_id="",
                prediction_id=prediction_id,
                model_version=eui.model_version,
                site_eui_kbtu_per_sqft=eui.value,
            )
        )

        return {"data": payload}


router = PredictionsController().router

__all__ = ["PredictionResponseEnvelope", "PredictionsController", "router"]
