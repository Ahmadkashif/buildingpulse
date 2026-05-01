"""Unit tests for :class:`PdfGenerationUseCaseService` — issue #81.

Pinned behaviours:

* When ``LeadResourceService.find_existing`` returns ``None``, the
  service raises :class:`PdfGatingError`. No prediction is recomputed,
  no HTML is rendered, no bytes are produced.
* When a lead exists, the service recomputes the prediction through
  :class:`PredictionResourceService`, builds a canonical
  :class:`~app.schemas.PredictionResponse`, hands the rendered HTML to
  the injected ``html_to_pdf`` callable, and returns the bytes plus a
  ``buildingpulse-report-<prediction_id>.pdf`` filename.
* The seam is the resource layer — fakes are substituted at
  ``LeadResourceService`` and ``PredictionResourceService``, never one
  level deeper at a repo or integration. ``html_to_pdf`` is the third
  seam (the WeasyPrint boundary), substituted with a recording fake.

Self-verification target: 100% branch coverage on the use-case module
under ``pytest --cov-branch``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
from app.domain.lead import Lead
from app.services.resource.prediction.service import PredictionResult
from app.services.usecase.pdf_generation.service import (
    PdfGatingError,
    PdfGenerationRequest,
    PdfGenerationUseCaseService,
)

# ---------------------------------------------------------------------------
# Fakes for the resource-service seams.
# ---------------------------------------------------------------------------


@dataclass
class FakeLeadResourceService:
    """Returns the scripted ``Lead`` (or ``None``) and records the lookup."""

    lead: Lead | None
    calls: list[dict[str, Any]] = field(default_factory=list)

    def find_existing(self, **kwargs: Any) -> Lead | None:
        self.calls.append(kwargs)
        return self.lead


@dataclass
class FakePredictionResourceService:
    """Returns a scripted :class:`PredictionResult` and records the call."""

    result: PredictionResult
    calls: list[dict[str, Any]] = field(default_factory=list)

    def predict(self, **kwargs: Any) -> PredictionResult:
        self.calls.append(kwargs)
        return self.result


@dataclass
class RecordingHtmlToPdf:
    """Records each HTML payload it sees and returns scripted bytes."""

    pdf: bytes = b"%PDF-1.7 fake-bytes\n"
    inputs: list[str] = field(default_factory=list)

    def __call__(self, html: str) -> bytes:
        self.inputs.append(html)
        return self.pdf


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _stub_lead(prediction_id: str = "pred_abc", email: str = "owner@example.com") -> Lead:
    now = datetime(2026, 4, 16, 14, 30, tzinfo=UTC)
    return Lead(
        id="lead_1",
        prediction_id=prediction_id,
        name="Owner",
        email=email,
        phone="+15551234567",
        role="owner",
        sponsor_id="sponsor_1",
        scenario_id=None,
        consent_given_at=now,
        fine_snapshot_usd=12_400.0,
        created_at=now,
        updated_at=now,
    )


def _stub_prediction_result() -> PredictionResult:
    from app.domain.ll97 import FineYear, Ll97Outlook
    from app.domain.peer import PeerCohort, PeerOutlook
    from app.domain.prediction import EuiPrediction
    from app.fixtures.stub_prediction import STUB

    pred = STUB["prediction"]
    peer_blob = STUB["peer"]
    ll97_blob = STUB["ll97"]

    eui = EuiPrediction(
        value=pred["siteEuiKbtuPerSqft"],
        low=pred["intervalLow"],
        high=pred["intervalHigh"],
        model_version=pred["modelVersion"],
    )
    peer = PeerOutlook(
        cohort=PeerCohort(
            property_type=peer_blob["cohort"]["propertyType"],
            borough=peer_blob["cohort"]["borough"],
            age_band=peer_blob["cohort"]["ageBand"],
        ),
        cohort_size=peer_blob["cohortSize"],
        median=peer_blob["medianSiteEui"],
        p25=peer_blob["p25SiteEui"],
        p75=peer_blob["p75SiteEui"],
        percentile=peer_blob["percentile"],
    )
    ll97 = Ll97Outlook(
        cap_current=ll97_blob["capKbtuPerSqft2024To2029"],
        cap_future=ll97_blob["capKbtuPerSqft2030To2034"],
        fine_current=ll97_blob["projectedAnnualFineUsd2024"],
        fine_future=ll97_blob["projectedAnnualFineUsd2030"],
        at_risk=ll97_blob["atRisk"],
        fine_series=tuple(
            FineYear(
                year=row["year"],
                projected_annual_fine_usd=row["projectedAnnualFineUsd"],
            )
            for row in ll97_blob["fineSeries"]
        ),
    )
    return PredictionResult(eui=eui, peer=peer, ll97=ll97)


def _stub_request(
    *,
    prediction_id: str = "pred_abc",
    email: str = "owner@example.com",
) -> PdfGenerationRequest:
    return PdfGenerationRequest(
        prediction_id=prediction_id,
        email=email,
        property_type="multifamily-housing",
        borough="brooklyn",
        gross_floor_area_sqft=45000,
        year_built=1925,
        number_of_buildings=1,
        generated_at=datetime(2026, 4, 16, 14, 30, tzinfo=UTC),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_raises_pdf_gating_error_when_no_lead_exists() -> None:
    lead_svc = FakeLeadResourceService(lead=None)
    pred_svc = FakePredictionResourceService(result=_stub_prediction_result())
    pdf = RecordingHtmlToPdf()
    svc = PdfGenerationUseCaseService(
        lead_service=lead_svc,
        prediction_service=pred_svc,
        html_to_pdf=pdf,
    )

    with pytest.raises(PdfGatingError) as excinfo:
        svc.generate(_stub_request(prediction_id="pred_xyz"))

    assert excinfo.value.prediction_id == "pred_xyz"
    assert "pred_xyz" in str(excinfo.value)
    # Gating happens *before* recomputation or rendering — short-circuit.
    assert pred_svc.calls == []
    assert pdf.inputs == []


def test_returns_pdf_bytes_and_filename_when_lead_exists() -> None:
    lead = _stub_lead(prediction_id="pred_abc", email="owner@example.com")
    lead_svc = FakeLeadResourceService(lead=lead)
    pred_svc = FakePredictionResourceService(result=_stub_prediction_result())
    pdf = RecordingHtmlToPdf(pdf=b"%PDF-1.7 ok\n")
    svc = PdfGenerationUseCaseService(
        lead_service=lead_svc,
        prediction_service=pred_svc,
        html_to_pdf=pdf,
    )

    result = svc.generate(_stub_request())

    assert result.pdf_bytes.startswith(b"%PDF-")
    assert result.pdf_bytes == b"%PDF-1.7 ok\n"
    assert result.filename == "buildingpulse-report-pred_abc.pdf"


def test_lead_lookup_uses_request_prediction_id_and_email() -> None:
    lead_svc = FakeLeadResourceService(
        lead=_stub_lead(prediction_id="pred_abc", email="owner@example.com")
    )
    pred_svc = FakePredictionResourceService(result=_stub_prediction_result())
    svc = PdfGenerationUseCaseService(
        lead_service=lead_svc,
        prediction_service=pred_svc,
        html_to_pdf=RecordingHtmlToPdf(),
    )

    svc.generate(_stub_request())

    assert lead_svc.calls == [{"prediction_id": "pred_abc", "email": "owner@example.com"}]


def test_recomputes_prediction_with_request_building_input() -> None:
    lead_svc = FakeLeadResourceService(lead=_stub_lead())
    pred_svc = FakePredictionResourceService(result=_stub_prediction_result())
    svc = PdfGenerationUseCaseService(
        lead_service=lead_svc,
        prediction_service=pred_svc,
        html_to_pdf=RecordingHtmlToPdf(),
    )

    svc.generate(_stub_request())

    assert pred_svc.calls == [
        {
            "property_type": "multifamily-housing",
            "borough": "brooklyn",
            "gross_floor_area_sqft": 45000,
            "year_built": 1925,
            "number_of_buildings": 1,
        }
    ]


def test_html_to_pdf_receives_rendered_template_html() -> None:
    lead_svc = FakeLeadResourceService(lead=_stub_lead())
    pred_svc = FakePredictionResourceService(result=_stub_prediction_result())
    pdf = RecordingHtmlToPdf()
    svc = PdfGenerationUseCaseService(
        lead_service=lead_svc,
        prediction_service=pred_svc,
        html_to_pdf=pdf,
    )

    svc.generate(_stub_request())

    assert len(pdf.inputs) == 1
    html = pdf.inputs[0]
    assert html.startswith("<!DOCTYPE html>")
    assert "Headline Metrics" in html
    # Prediction id is threaded into the report header.
    assert "pred_abc" in html


def test_real_weasyprint_adapter_produces_pdf_magic_bytes() -> None:
    """The default ``render_pdf_with_weasyprint`` produces real PDF bytes."""
    from app.services.usecase.pdf_generation.service import render_pdf_with_weasyprint

    pdf = render_pdf_with_weasyprint("<html><body>hi</body></html>")

    assert pdf.startswith(b"%PDF-")
