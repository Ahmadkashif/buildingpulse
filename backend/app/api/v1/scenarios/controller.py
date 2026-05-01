"""GET /api/predictions/{prediction_id}/scenarios — controller.

Returns the retrofit scenario list for a single prediction. Each entry
echoes the static library fields (``id``, ``name``, ``description``,
``reductionPct``, ``costLow``, ``costHigh``, ``citation``) and adds the
recomputed LL97 fine projection (``recomputedFineSeries``,
``recomputedFine2024``, ``recomputedFine2030``).

Lookup vs. recompute (documented choice)
----------------------------------------
The MVP does not persist predictions server-side — the diagnostic call
(``POST /api/predictions``) returns the full payload to the client and
the frontend caches it in TanStack Query. Adding a prediction store just
to feed this endpoint would expand scope beyond this issue.

Instead, the controller **recomputes from input passed alongside the
request**: the ``prediction_id`` in the path is opaque (it is forwarded
to audit / lead capture) and the building inputs the engine actually
needs — ``propertyType``, ``predictedEui``, ``grossFloorAreaSqft`` —
travel as query parameters. The frontend already has these values in
its prediction cache.

Server-side ungated per the PRD: gating retrofit scenarios is a UX
concern (the lead modal), not a security concern.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.deps import (
    get_audit_service,
    get_request_id,
    get_scenario_service,
    get_trace_id,
)
from app.domain.audit import ScenarioSelected
from app.schemas import FineYear, PropertyType
from app.services.resource.audit.service import AuditService
from app.services.resource.scenario.service import ScenarioResourceService

_DEDUPE_WINDOW = timedelta(seconds=5)

_PREDICTION_ID_PATTERN = re.compile(r"^pred_[A-Za-z0-9]+$")


class ScenarioPublic(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    reduction_pct: float = Field(gt=0.0, le=1.0)
    cost_low: float = Field(ge=0.0)
    cost_high: float = Field(ge=0.0)
    recomputed_fine_series: list[FineYear] = Field(min_length=1)
    recomputed_fine2024: float = Field(ge=0.0)
    recomputed_fine2030: float = Field(ge=0.0)
    citation: str = Field(min_length=1)


class ScenariosResponseEnvelope(BaseModel):
    data: list[ScenarioPublic]


class ScenarioSelectRequest(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    prediction_id: str = Field(min_length=1)


class ScenarioSelectResult(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )

    prediction_id: str
    scenario_id: str
    deduped: bool


class ScenarioSelectEnvelope(BaseModel):
    data: ScenarioSelectResult


class ScenariosController:
    """Owns the `/api/predictions/{prediction_id}/scenarios` router."""

    def __init__(self) -> None:
        self.router = APIRouter()
        self.router.add_api_route(
            "/predictions/{prediction_id}/scenarios",
            self.list,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            response_model=ScenariosResponseEnvelope,
            response_model_by_alias=True,
        )
        self.router.add_api_route(
            "/scenarios/{scenario_id}/select",
            self.select,
            methods=["POST"],
            status_code=status.HTTP_200_OK,
            response_model=ScenarioSelectEnvelope,
            response_model_by_alias=True,
        )

    async def list(
        self,
        prediction_id: Annotated[str, Path(min_length=1)],
        property_type: Annotated[PropertyType, Query(alias="propertyType")],
        predicted_eui: Annotated[float, Query(alias="predictedEui", gt=0.0)],
        gross_floor_area_sqft: Annotated[float, Query(alias="grossFloorAreaSqft", gt=0.0)],
        scenario_service: Annotated[ScenarioResourceService, Depends(get_scenario_service)],
    ) -> dict[str, Any]:
        if _PREDICTION_ID_PATTERN.fullmatch(prediction_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"prediction {prediction_id!r} not found",
            )

        scenarios = scenario_service.list(
            property_type=property_type,
            baseline_eui_kbtu_per_sqft=predicted_eui,
            gross_floor_area_sqft=gross_floor_area_sqft,
        )

        items: list[dict[str, Any]] = []
        for scenario in scenarios:
            outlook = scenario.outlook
            items.append(
                {
                    "id": scenario.id,
                    "name": scenario.name,
                    "description": scenario.description,
                    "reductionPct": scenario.reduction_pct,
                    "costLow": scenario.cost_low_usd_per_sqft,
                    "costHigh": scenario.cost_high_usd_per_sqft,
                    "recomputedFineSeries": [
                        {
                            "year": row.year,
                            "projectedAnnualFineUsd": row.projected_annual_fine_usd,
                        }
                        for row in outlook.fine_series
                    ],
                    "recomputedFine2024": outlook.fine_current,
                    "recomputedFine2030": outlook.fine_future,
                    "citation": scenario.citation,
                }
            )
        return {"data": items}

    async def select(
        self,
        scenario_id: Annotated[str, Path(min_length=1)],
        body: ScenarioSelectRequest,
        scenario_service: Annotated[ScenarioResourceService, Depends(get_scenario_service)],
        audit: Annotated[AuditService, Depends(get_audit_service)],
    ) -> dict[str, Any]:
        if _PREDICTION_ID_PATTERN.fullmatch(body.prediction_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"prediction {body.prediction_id!r} not found",
            )
        if not scenario_service.is_known_scenario_id(scenario_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"scenario {scenario_id!r} not found",
            )

        now = datetime.now(UTC)
        since_iso = (now - _DEDUPE_WINDOW).isoformat()
        deduped = audit.scenario_selected_recently(
            prediction_id=body.prediction_id,
            scenario_id=scenario_id,
            since_iso=since_iso,
        )
        if not deduped:
            await audit.record(
                ScenarioSelected(
                    occurred_at=now,
                    request_id=get_request_id(),
                    trace_id=get_trace_id(),
                    actor_session_id="",
                    prediction_id=body.prediction_id,
                    scenario_id=scenario_id,
                )
            )
        return {
            "data": {
                "predictionId": body.prediction_id,
                "scenarioId": scenario_id,
                "deduped": deduped,
            }
        }


router = ScenariosController().router

__all__ = [
    "ScenarioPublic",
    "ScenarioSelectEnvelope",
    "ScenarioSelectRequest",
    "ScenarioSelectResult",
    "ScenariosController",
    "ScenariosResponseEnvelope",
    "router",
]
