"""GET /api/predictions/{prediction_id}/pdf — controller.

Thin HTTP shell over :class:`PdfGenerationUseCaseService`:

* The use-case raises :class:`PdfGatingError` when no lead exists for the
  ``(prediction_id, email)`` pair; the controller maps that to ``403``.
* On success the controller streams the bytes back as
  ``application/pdf`` with a ``Content-Disposition: attachment`` header
  using the ``building-pulse-<prediction_id>.pdf`` filename the issue
  specifies, and records a :class:`PdfGenerated` audit row.

The MVP does not persist predictions server-side, so the building inputs
needed to recompute the report ride along as query parameters — same
convention the scenarios endpoint uses.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import Response

from app.deps import (
    get_audit_service,
    get_pdf_generation_use_case,
    get_request_id,
    get_trace_id,
)
from app.domain.audit import PdfGenerated
from app.schemas import Borough, PropertyType
from app.services.resource.audit.service import AuditService
from app.services.usecase.pdf_generation.service import (
    PdfGatingError,
    PdfGenerationRequest,
    PdfGenerationUseCaseService,
)


class PdfController:
    """Owns the `/api/predictions/{prediction_id}/pdf` router."""

    def __init__(self) -> None:
        self.router = APIRouter()
        self.router.add_api_route(
            "/predictions/{prediction_id}/pdf",
            self.get,
            methods=["GET"],
            status_code=status.HTTP_200_OK,
            response_class=Response,
        )

    async def get(
        self,
        prediction_id: Annotated[str, Path(min_length=1)],
        email: Annotated[str, Query(min_length=1)],
        property_type: Annotated[PropertyType, Query(alias="propertyType")],
        borough: Annotated[Borough, Query()],
        gross_floor_area_sqft: Annotated[
            int, Query(alias="grossFloorAreaSqft", ge=500, le=5_000_000)
        ],
        year_built: Annotated[int, Query(alias="yearBuilt", ge=1800, le=2026)],
        number_of_buildings: Annotated[int, Query(alias="numberOfBuildings", ge=1, le=10)],
        use_case: Annotated[PdfGenerationUseCaseService, Depends(get_pdf_generation_use_case)],
        audit: Annotated[AuditService, Depends(get_audit_service)],
    ) -> Response:
        now = datetime.now(UTC)
        request = PdfGenerationRequest(
            prediction_id=prediction_id,
            email=email,
            property_type=property_type,
            borough=borough,
            gross_floor_area_sqft=gross_floor_area_sqft,
            year_built=year_built,
            number_of_buildings=number_of_buildings,
            generated_at=now,
        )
        try:
            result = use_case.generate(request)
        except PdfGatingError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"no lead on file for prediction_id={exc.prediction_id!r}",
            ) from exc

        await audit.record(
            PdfGenerated(
                occurred_at=now,
                request_id=get_request_id(),
                trace_id=get_trace_id(),
                actor_session_id="",
                prediction_id=prediction_id,
                bytes_size=len(result.pdf_bytes),
            )
        )

        filename = f"building-pulse-{prediction_id}.pdf"
        return Response(
            content=result.pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )


router = PdfController().router

__all__ = ["PdfController", "router"]
