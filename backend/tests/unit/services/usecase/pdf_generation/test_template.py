"""Snapshot + behavioural tests for the HTML report template.

The renderer is deterministic by construction — same ``PredictionResponse``
in, byte-identical HTML out. The snapshot in ``snapshots/stub_prediction.html``
is the contract: any change to the template that affects the canonical
fixture must be reflected by regenerating the snapshot.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from app.fixtures.stub_prediction import STUB
from app.schemas import PredictionResponse
from app.services.usecase.pdf_generation import render_report_html

SNAPSHOT_PATH = Path(__file__).parent / "snapshots" / "stub_prediction.html"


@pytest.fixture
def stub_prediction() -> PredictionResponse:
    return PredictionResponse.model_validate(STUB)


def test_renders_against_any_valid_prediction_response(
    stub_prediction: PredictionResponse,
) -> None:
    """Renderer accepts a fully-validated ``PredictionResponse`` and returns HTML."""
    html = render_report_html(stub_prediction)
    assert html.startswith("<!DOCTYPE html>")
    assert html.rstrip().endswith("</html>")


def test_snapshot_pinned_to_fixture(stub_prediction: PredictionResponse) -> None:
    """Re-rendering the canonical fixture produces zero diff against the snapshot."""
    rendered = render_report_html(stub_prediction)
    expected = SNAPSHOT_PATH.read_text(encoding="utf-8")
    assert rendered == expected, (
        "HTML snapshot drifted. If this change is intentional, regenerate "
        f"{SNAPSHOT_PATH.relative_to(Path.cwd())} from the stub fixture."
    )


def test_renderer_is_deterministic(stub_prediction: PredictionResponse) -> None:
    """Two calls with the same input return the exact same string."""
    assert render_report_html(stub_prediction) == render_report_html(stub_prediction)


def test_self_contained_no_external_assets(
    stub_prediction: PredictionResponse,
) -> None:
    """No ``<link>`` / ``<script src>`` / ``<img src=http>`` — CSS is embedded."""
    html = render_report_html(stub_prediction)
    assert "<link" not in html.lower()
    assert "<script" not in html.lower()
    assert "http://" not in html
    assert "https://" not in html
    assert "<style>" in html


def test_layout_sections_present(stub_prediction: PredictionResponse) -> None:
    """Every section the report page shows has a corresponding marker in the PDF HTML."""
    html = render_report_html(stub_prediction)
    assert "sponsor-strip" in html
    assert "Headline Metrics" in html
    assert "Predicted Site EUI" in html
    assert "Peer Percentile" in html
    assert "LL97 Status" in html
    assert "Peer Cohort Comparison" in html
    assert "LL97 Fine Outlook" in html
    assert "Building Profile" in html


def test_kpi_values_rendered_from_input(
    stub_prediction: PredictionResponse,
) -> None:
    """KPI numbers come from the prediction, formatted consistently."""
    html = render_report_html(stub_prediction)
    # Predicted EUI: 87.3 kBtu/sf
    assert "87.3 kBtu/sf" in html
    # Interval bounds
    assert "65.2" in html
    assert "109.4" in html
    # Percentile with ordinal suffix
    assert "68th" in html
    # At-risk LL97 status with money-formatted projected fine
    assert "At Risk" in html
    assert "$12,400" in html


def test_all_fine_series_years_present(
    stub_prediction: PredictionResponse,
) -> None:
    """The full year-by-year LL97 fine timeline is in the document."""
    html = render_report_html(stub_prediction)
    for row in stub_prediction.ll97.fine_series:
        assert f"<td>{row.year}</td>" in html


def test_html_escapes_user_supplied_strings() -> None:
    """Free-form strings (id, model_version) are HTML-escaped to prevent injection."""
    payload = {
        **STUB,
        "id": "<script>alert(1)</script>",
        "prediction": {**STUB["prediction"], "modelVersion": "v1 & <hax>"},
    }
    html = render_report_html(PredictionResponse.model_validate(payload))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert "v1 &amp; &lt;hax&gt;" in html


def test_compliant_building_renders_without_at_risk_marker() -> None:
    """When ``at_risk`` is False, status reads 'Compliant' and uses the compliant class."""
    payload = {
        **STUB,
        "ll97": {
            **STUB["ll97"],
            "atRisk": False,
            "projectedAnnualFineUsd2030": 0,
            "fineSeries": [{"year": y, "projectedAnnualFineUsd": 0} for y in range(2026, 2035)],
        },
    }
    html = render_report_html(PredictionResponse.model_validate(payload))
    assert "Compliant" in html
    assert 'class="kpi kpi--compliant"' in html
    assert 'class="kpi kpi--at-risk"' not in html
    assert "Below current cap" in html
