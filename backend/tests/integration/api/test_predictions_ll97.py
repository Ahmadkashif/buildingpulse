"""Integration: ``POST /api/predictions`` returns a real ``ll97`` block.

Three exposure regimes are exercised end-to-end through the live FastAPI
app by overriding the prediction service so each request returns a known
predicted EUI:

* **Under cap** — predicted EUI low enough that even the 2030-2034 cap is
  not exceeded; every fine in the series is zero and ``atRisk`` is False.
* **Straddling** — predicted EUI in the band where the 2024-2029 cap is
  met but the tighter 2030-2034 cap is breached; the series is flat zero
  through 2029 then jumps at 2030.
* **Over cap** — predicted EUI breaches both caps; every fine in the
  series is positive and the 2030 step is strictly larger than the 2024
  fine.

The series spans the current calendar year through 2034 inclusive in
ascending order; values are flat within each compliance period.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from app.deps import get_prediction_service
from app.domain.ll97 import compute as compute_ll97
from app.domain.peer.types import PeerCohort, PeerOutlook
from app.domain.prediction.types import EuiPrediction
from app.services.resource.prediction.service import (
    PredictionResult,
)
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    from app.main import app

    monkeypatch.setenv("DB_PATH", str(tmp_path / "buildingpulse.db"))
    with TestClient(app) as c:
        yield c


VALID_BODY: dict[str, Any] = {
    "propertyType": "office",
    "borough": "manhattan",
    "grossFloorAreaSqft": 50000,
    "yearBuilt": 1985,
    "numberOfBuildings": 1,
}


class _StubPredictionService:
    """Returns a fixed EUI so we can pin the LL97 outlook deterministically.

    Real artifacts power peer + ll97; only the EUI value is controlled.
    """

    def __init__(self, eui_value: float) -> None:
        self._eui_value = eui_value

    def predict(
        self,
        *,
        property_type: str,
        borough: str,
        gross_floor_area_sqft: int,
        year_built: int,
        number_of_buildings: int,
    ) -> PredictionResult:
        eui = EuiPrediction(
            value=self._eui_value,
            low=self._eui_value - 5.0,
            high=self._eui_value + 5.0,
            model_version="stub-v1",
        )
        peer = PeerOutlook(
            cohort=PeerCohort(property_type=property_type, borough=borough, age_band="1980-1999"),
            cohort_size=42,
            median=self._eui_value,
            p25=self._eui_value - 5.0,
            p75=self._eui_value + 5.0,
            percentile=50,
        )
        ll97 = compute_ll97(
            property_type=property_type,
            predicted_eui_kbtu_per_sqft=self._eui_value,
            gross_floor_area_sqft=float(gross_floor_area_sqft),
        )
        return PredictionResult(eui=eui, peer=peer, ll97=ll97)


def _override(service: _StubPredictionService) -> None:
    from app.main import app

    def _resolve() -> _StubPredictionService:
        return service

    app.dependency_overrides[get_prediction_service] = _resolve


def _clear_override() -> None:
    from app.main import app

    app.dependency_overrides.pop(get_prediction_service, None)


CURRENT_YEAR = date.today().year


class TestFineSeriesShape:
    def test_series_spans_current_year_through_2034_ascending(self, client: TestClient) -> None:
        _override(_StubPredictionService(eui_value=80.0))
        try:
            response = client.post("/api/predictions", json=VALID_BODY)
        finally:
            _clear_override()

        assert response.status_code == 201
        series = response.json()["data"]["ll97"]["fineSeries"]
        years = [row["year"] for row in series]
        assert years == list(range(CURRENT_YEAR, 2035))
        assert years == sorted(years)


class TestUnderCap:
    """An EUI well under the 2030-2034 cap → every fine is zero."""

    def test_series_is_flat_zero_and_at_risk_false(self, client: TestClient) -> None:
        # Office cap_2030_2034 = 0.00453 tCO2e/gsf; coefficient = 6.81e-5;
        # break-even EUI ≈ 66.5 kBTU/gsf. 30 is comfortably under both caps.
        _override(_StubPredictionService(eui_value=30.0))
        try:
            response = client.post("/api/predictions", json=VALID_BODY)
        finally:
            _clear_override()

        body = response.json()["data"]["ll97"]
        assert body["atRisk"] is False
        assert body["projectedAnnualFineUsd2024"] == 0
        assert body["projectedAnnualFineUsd2030"] == 0
        assert all(row["projectedAnnualFineUsd"] == 0 for row in body["fineSeries"])


class TestStraddling:
    """An EUI between the two caps → flat zero through 2029, then steps up."""

    def test_series_zero_then_positive_at_2030(self, client: TestClient) -> None:
        # Office cap_2024_2029 ≈ 124 kBTU/gsf-equivalent break-even,
        # cap_2030_2034 ≈ 66.5. EUI = 100 sits in the straddle zone.
        _override(_StubPredictionService(eui_value=100.0))
        try:
            response = client.post("/api/predictions", json=VALID_BODY)
        finally:
            _clear_override()

        body = response.json()["data"]["ll97"]
        series = body["fineSeries"]
        early = [r for r in series if r["year"] < 2030]
        late = [r for r in series if r["year"] >= 2030]

        assert body["atRisk"] is True
        assert body["projectedAnnualFineUsd2024"] == 0
        assert body["projectedAnnualFineUsd2030"] > 0
        assert all(r["projectedAnnualFineUsd"] == 0 for r in early)
        assert all(r["projectedAnnualFineUsd"] > 0 for r in late)
        # Each segment must be flat within itself.
        assert len({r["projectedAnnualFineUsd"] for r in early}) == 1
        assert len({r["projectedAnnualFineUsd"] for r in late}) == 1


class TestOverCap:
    """An EUI over both caps → series positive throughout, jump at 2030."""

    def test_series_positive_with_step_at_2030(self, client: TestClient) -> None:
        _override(_StubPredictionService(eui_value=200.0))
        try:
            response = client.post("/api/predictions", json=VALID_BODY)
        finally:
            _clear_override()

        body = response.json()["data"]["ll97"]
        series = body["fineSeries"]
        early = [r for r in series if r["year"] < 2030]
        late = [r for r in series if r["year"] >= 2030]

        assert body["atRisk"] is True
        assert body["projectedAnnualFineUsd2024"] > 0
        assert body["projectedAnnualFineUsd2030"] > body["projectedAnnualFineUsd2024"]
        # Flat within each compliance period, with a strict step at 2030.
        assert len({r["projectedAnnualFineUsd"] for r in early}) == 1
        assert len({r["projectedAnnualFineUsd"] for r in late}) == 1
        assert late[0]["projectedAnnualFineUsd"] > early[-1]["projectedAnnualFineUsd"]
