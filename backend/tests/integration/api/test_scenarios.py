"""Integration: ``GET /api/predictions/{prediction_id}/scenarios``.

Exercises the live FastAPI app:

* Happy path returns 200 with a stably ordered list of cited scenarios,
  each carrying the documented camelCase fields.
* An ``unknown`` prediction id (does not match the ``pred_<hex>`` shape
  the diagnostic endpoint emits) returns 404.
* Unsupported ``propertyType`` values are rejected upstream by FastAPI's
  query-param validation (422), and a missing ``predictedEui`` likewise.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from app.policy.retrofits import LIBRARY
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    from app.main import app

    monkeypatch.setenv("DB_PATH", str(tmp_path / "buildingpulse.db"))
    with TestClient(app) as c:
        yield c


HAPPY_QUERY: dict[str, Any] = {
    "propertyType": "office",
    "predictedEui": 200.0,
    "grossFloorAreaSqft": 50000,
}


CURRENT_YEAR = date.today().year


class TestHappyPath:
    def test_returns_200_with_one_entry_per_library_intervention(self, client: TestClient) -> None:
        response = client.get("/api/predictions/pred_abc123/scenarios", params=HAPPY_QUERY)

        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"data"}
        items = body["data"]
        assert len(items) == len(LIBRARY["office"])

    def test_each_entry_has_documented_shape(self, client: TestClient) -> None:
        response = client.get("/api/predictions/pred_abc123/scenarios", params=HAPPY_QUERY)
        assert response.status_code == 200
        items = response.json()["data"]

        expected_keys = {
            "id",
            "name",
            "description",
            "reductionPct",
            "costLow",
            "costHigh",
            "recomputedFineSeries",
            "recomputedFine2024",
            "recomputedFine2030",
            "citation",
        }
        for item in items:
            assert set(item.keys()) == expected_keys
            assert item["id"]
            assert item["name"]
            assert item["description"]
            assert 0.0 < item["reductionPct"] <= 1.0
            assert item["costLow"] >= 0.0
            assert item["costHigh"] >= item["costLow"]
            assert item["citation"]
            series = item["recomputedFineSeries"]
            assert series, "fineSeries must not be empty"
            years = [row["year"] for row in series]
            assert years == list(range(CURRENT_YEAR, 2035))
            assert all(row["projectedAnnualFineUsd"] >= 0 for row in series)

    def test_ordering_is_stable_and_matches_engine(self, client: TestClient) -> None:
        first = client.get("/api/predictions/pred_abc123/scenarios", params=HAPPY_QUERY)
        second = client.get("/api/predictions/pred_zzz/scenarios", params=HAPPY_QUERY)
        assert first.status_code == 200
        assert second.status_code == 200

        ids_first = [s["id"] for s in first.json()["data"]]
        ids_second = [s["id"] for s in second.json()["data"]]
        assert ids_first == ids_second

        # Engine sorts by total recomputed fine ascending — verify monotonic.
        items = first.json()["data"]
        totals = [s["recomputedFine2024"] + s["recomputedFine2030"] for s in items]
        assert totals == sorted(totals)

    def test_recomputed_fines_are_lower_than_baseline_for_at_risk_building(
        self, client: TestClient
    ) -> None:
        # Office baseline EUI of 200 is comfortably over both LL97 caps,
        # so every retrofit's recomputed total fine must be lower than
        # the baseline total.
        from app.domain.ll97 import compute as compute_ll97

        baseline = compute_ll97(
            property_type="office",
            predicted_eui_kbtu_per_sqft=200.0,
            gross_floor_area_sqft=50000.0,
        )
        baseline_total = baseline.fine_current + baseline.fine_future
        assert baseline_total > 0

        response = client.get("/api/predictions/pred_abc123/scenarios", params=HAPPY_QUERY)
        assert response.status_code == 200
        for item in response.json()["data"]:
            recomputed = item["recomputedFine2024"] + item["recomputedFine2030"]
            assert recomputed < baseline_total


class TestUnknownPredictionId:
    def test_id_without_pred_prefix_returns_404(self, client: TestClient) -> None:
        response = client.get("/api/predictions/not-a-real-id/scenarios", params=HAPPY_QUERY)
        assert response.status_code == 404

    def test_empty_suffix_after_pred_prefix_returns_404(self, client: TestClient) -> None:
        # The diagnostic endpoint always emits `pred_<hex>`; bare `pred_`
        # is not a valid id.
        response = client.get("/api/predictions/pred_/scenarios", params=HAPPY_QUERY)
        assert response.status_code == 404


class TestQueryValidation:
    def test_missing_predicted_eui_returns_422(self, client: TestClient) -> None:
        params = {k: v for k, v in HAPPY_QUERY.items() if k != "predictedEui"}
        response = client.get("/api/predictions/pred_abc123/scenarios", params=params)
        assert response.status_code == 422

    def test_unsupported_property_type_returns_422(self, client: TestClient) -> None:
        params = {**HAPPY_QUERY, "propertyType": "warehouse"}
        response = client.get("/api/predictions/pred_abc123/scenarios", params=params)
        assert response.status_code == 422

    def test_zero_sqft_returns_422(self, client: TestClient) -> None:
        params = {**HAPPY_QUERY, "grossFloorAreaSqft": 0}
        response = client.get("/api/predictions/pred_abc123/scenarios", params=params)
        assert response.status_code == 422
