"""PdfGenerationUseCaseService — lead-gated server-rendered PDF.

Workflow (prd.md §"PDF rendering" + §"Lead capture / Gating"; issue #81):

1. Look up an existing lead for the ``(prediction_id, email)`` pair via
   :class:`LeadResourceService.find_existing`. Without a lead the
   download is forbidden — raise :class:`PdfGatingError` so the
   controller layer can map it to ``403``. Gating is a server-side
   check; the frontend mirror is UX-only.
2. Recompose the prediction through :class:`PredictionResourceService`
   so the rendered report reflects the canonical model output rather
   than whatever client-supplied snapshot reached the endpoint.
3. Shape the result into a :class:`~app.schemas.PredictionResponse` —
   the same envelope ``GET /api/predictions/:id`` would return — and
   hand it to :func:`render_report_html`.
4. Convert the deterministic HTML to PDF bytes through the injected
   ``html_to_pdf`` callable. The default is :func:`render_pdf_with_weasyprint`,
   which loads WeasyPrint lazily so unit tests can substitute a fake at
   the seam without paying the import cost.

The service holds no repos and no integrations directly — the
``usecases-compose-resources-only`` import-linter contract enforces that.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.schemas import PredictionResponse
from app.services.resource.lead.service import LeadResourceService
from app.services.resource.prediction.service import PredictionResourceService
from app.services.usecase.pdf_generation.template import render_report_html

__all__ = [
    "PdfGatingError",
    "PdfGenerationRequest",
    "PdfGenerationResult",
    "PdfGenerationUseCaseService",
    "render_pdf_with_weasyprint",
]


class PdfGatingError(Exception):
    """Raised when no lead exists for the prediction id requesting a PDF.

    The controller layer maps this to a ``403 Forbidden``. The exception
    carries ``prediction_id`` so structured logs and the audit trail can
    pin the failed download to a specific report.
    """

    def __init__(self, prediction_id: str) -> None:
        self.prediction_id = prediction_id
        super().__init__(
            f"no lead found for prediction_id={prediction_id!r}; PDF download is gated"
        )


@dataclass(frozen=True, slots=True)
class PdfGenerationRequest:
    """Inputs the use-case needs to produce a single PDF.

    ``email`` participates in the lead-gating lookup — the idempotency
    window is keyed on ``(prediction_id, email)``. The five building
    fields drive the recomputed prediction; we re-run the model rather
    than trust a client-supplied snapshot so the PDF cannot be forged
    from a manipulated payload.
    """

    prediction_id: str
    email: str
    property_type: str
    borough: str
    gross_floor_area_sqft: int
    year_built: int
    number_of_buildings: int
    generated_at: datetime


@dataclass(frozen=True, slots=True)
class PdfGenerationResult:
    """Bytes plus the suggested ``Content-Disposition`` filename."""

    pdf_bytes: bytes
    filename: str


class PdfGenerationUseCaseService:
    """Composes lead-gating + prediction + template + WeasyPrint."""

    def __init__(
        self,
        *,
        lead_service: LeadResourceService,
        prediction_service: PredictionResourceService,
        html_to_pdf: Callable[[str], bytes],
    ) -> None:
        self._lead = lead_service
        self._prediction = prediction_service
        self._html_to_pdf = html_to_pdf

    def generate(self, request: PdfGenerationRequest) -> PdfGenerationResult:
        existing = self._lead.find_existing(
            prediction_id=request.prediction_id, email=request.email
        )
        if existing is None:
            raise PdfGatingError(request.prediction_id)

        result = self._prediction.predict(
            property_type=request.property_type,
            borough=request.borough,
            gross_floor_area_sqft=request.gross_floor_area_sqft,
            year_built=request.year_built,
            number_of_buildings=request.number_of_buildings,
        )

        response = _build_prediction_response(request, result)
        html = render_report_html(response)
        pdf_bytes = self._html_to_pdf(html)
        filename = f"buildingpulse-report-{request.prediction_id}.pdf"
        return PdfGenerationResult(pdf_bytes=pdf_bytes, filename=filename)


def _build_prediction_response(request: PdfGenerationRequest, result: Any) -> PredictionResponse:
    eui = result.eui
    peer = result.peer
    ll97 = result.ll97
    payload: dict[str, Any] = {
        "id": request.prediction_id,
        "generatedAt": request.generated_at.isoformat(),
        "input": {
            "propertyType": request.property_type,
            "borough": request.borough,
            "grossFloorAreaSqft": request.gross_floor_area_sqft,
            "yearBuilt": request.year_built,
            "numberOfBuildings": request.number_of_buildings,
        },
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
    return PredictionResponse.model_validate(payload)


def render_pdf_with_weasyprint(html: str) -> bytes:
    """Production ``html_to_pdf`` adapter — lazy import keeps tests light."""
    from weasyprint import HTML

    return bytes(HTML(string=html).write_pdf())
