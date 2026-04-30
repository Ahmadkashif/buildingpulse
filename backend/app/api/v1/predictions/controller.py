"""POST /api/predictions — Phase 1 stub controller.

Hands back the canonical stub payload with a freshly generated `id` and
`generatedAt`, echoing the validated request body as `input`. After a
successful response is shaped, the controller records a
`PredictionGenerated` audit event tagged with the same `request_id` that
appears on the request's structured log line.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.deps import get_audit_service, get_request_id, get_trace_id
from app.domain.audit.types import PredictionGenerated
from app.fixtures.stub_prediction import STUB
from app.schemas import CreateBuildingInput, PredictionResponse
from app.services.resource.audit.service import AuditService


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
    ) -> dict[str, Any]:
        prediction_id = f"pred_{uuid4().hex}"
        generated_at = datetime.now(UTC)
        payload: dict[str, Any] = {
            "id": prediction_id,
            "generatedAt": generated_at.isoformat(),
            "input": body.model_dump(by_alias=True),
            "prediction": STUB["prediction"],
            "peer": STUB["peer"],
            "ll97": STUB["ll97"],
        }

        await audit.record(
            PredictionGenerated(
                occurred_at=generated_at,
                request_id=get_request_id(),
                trace_id=get_trace_id(),
                actor_session_id="",
                prediction_id=prediction_id,
                model_version=STUB["prediction"]["modelVersion"],
                site_eui_kbtu_per_sqft=STUB["prediction"]["siteEuiKbtuPerSqft"],
            )
        )

        return {"data": payload}


router = PredictionsController().router

__all__ = ["PredictionResponseEnvelope", "PredictionsController", "router"]
