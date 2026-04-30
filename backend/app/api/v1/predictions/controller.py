"""POST /api/predictions — Phase 1 stub controller.

Hands back the canonical stub payload with a freshly generated `id` and
`generatedAt`, echoing the validated request body as `input`. No business
logic lives here; later phases replace the stub blocks with real outputs.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.fixtures.stub_prediction import STUB
from app.schemas import CreateBuildingInput, PredictionResponse


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

    def create(self, body: CreateBuildingInput) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": f"pred_{uuid4().hex}",
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "input": body.model_dump(by_alias=True),
            "prediction": STUB["prediction"],
            "peer": STUB["peer"],
            "ll97": STUB["ll97"],
        }
        return {"data": payload}


router = PredictionsController().router

__all__ = ["PredictionResponseEnvelope", "PredictionsController", "router"]
