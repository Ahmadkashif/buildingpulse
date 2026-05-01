"""Pillars for the success path of `POST /api/predictions`.

Validation failures live in `test_api_predictions_validation.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from app.schemas import PredictionResponse
from fastapi.testclient import TestClient


class TestStatusAndShape:
    def test_returns_201_on_valid_body(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        response = client.post("/api/predictions", json=valid_request_body)
        assert response.status_code == 201

    def test_response_body_validates_against_schema(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        response = client.post("/api/predictions", json=valid_request_body)
        # Handler wraps in `{"data": ...}` per the Contract (the frontend
        # unwraps via ApiResponse<T>).
        envelope = response.json()
        assert "data" in envelope
        PredictionResponse.model_validate(envelope["data"])


class TestInputEcho:
    def test_response_input_equals_request_body(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        response = client.post("/api/predictions", json=valid_request_body)
        echoed = response.json()["data"]["input"]
        assert echoed == valid_request_body

    def test_response_input_reflects_modified_request(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        modified = {**valid_request_body, "yearBuilt": 2001, "numberOfBuildings": 3}
        response = client.post("/api/predictions", json=modified)
        echoed = response.json()["data"]["input"]
        assert echoed["yearBuilt"] == 2001
        assert echoed["numberOfBuildings"] == 3


class TestIdGeneration:
    def test_id_begins_with_pred_prefix(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        response = client.post("/api/predictions", json=valid_request_body)
        assert response.json()["data"]["id"].startswith("pred_")

    def test_two_calls_produce_distinct_ids(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        first = client.post("/api/predictions", json=valid_request_body).json()["data"]["id"]
        second = client.post("/api/predictions", json=valid_request_body).json()["data"]["id"]
        assert first != second


class TestGeneratedAt:
    def test_generated_at_is_recent(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        before = datetime.now(UTC)
        response = client.post("/api/predictions", json=valid_request_body)
        after = datetime.now(UTC)

        raw = response.json()["data"]["generatedAt"]
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)

        # Generated within the request window ±5s tolerance for slow CI.
        assert (before.timestamp() - 5) <= parsed.timestamp() <= (after.timestamp() + 5)

    def test_two_calls_produce_distinct_generated_at(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        # Same-millisecond collisions are theoretically possible; the handler
        # should produce strictly monotonic timestamps OR include enough
        # precision that back-to-back calls differ.
        first = client.post("/api/predictions", json=valid_request_body).json()["data"][
            "generatedAt"
        ]
        second = client.post("/api/predictions", json=valid_request_body).json()["data"][
            "generatedAt"
        ]
        assert first != second


class TestLL97BlockShape:
    """`ll97` is now produced by the real domain calculator (Phase 6).

    The block carries the period caps, the projected fines for each
    period, the ``atRisk`` verdict, and the per-year ``fineSeries`` from
    the current calendar year through 2034 inclusive.
    """

    def test_ll97_block_carries_required_keys(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        response = client.post("/api/predictions", json=valid_request_body)
        ll97 = response.json()["data"]["ll97"]
        assert set(ll97.keys()) == {
            "capKbtuPerSqft2024To2029",
            "capKbtuPerSqft2030To2034",
            "projectedAnnualFineUsd2024",
            "projectedAnnualFineUsd2030",
            "atRisk",
            "fineSeries",
        }
        assert isinstance(ll97["atRisk"], bool)


class TestRealPrediction:
    """`prediction` is now produced by the real model + ArtifactRegistry."""

    def test_prediction_varies_with_sqft(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        small = client.post(
            "/api/predictions", json={**valid_request_body, "grossFloorAreaSqft": 20000}
        ).json()["data"]["prediction"]["siteEuiKbtuPerSqft"]
        large = client.post(
            "/api/predictions", json={**valid_request_body, "grossFloorAreaSqft": 40000}
        ).json()["data"]["prediction"]["siteEuiKbtuPerSqft"]
        assert small != large

    def test_model_version_matches_metrics_json(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        import json
        from pathlib import Path

        metrics = json.loads(
            (Path(__file__).resolve().parents[1] / "artifacts" / "metrics.json").read_text()
        )
        response = client.post("/api/predictions", json=valid_request_body)
        assert response.json()["data"]["prediction"]["modelVersion"] == metrics["modelVersion"]

    def test_interval_is_pred_plus_minus_one_point_five_rmse(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        import json
        from pathlib import Path

        metrics = json.loads(
            (Path(__file__).resolve().parents[1] / "artifacts" / "metrics.json").read_text()
        )
        rmse = float(metrics["rmse"])

        block = client.post("/api/predictions", json=valid_request_body).json()["data"][
            "prediction"
        ]
        value = float(block["siteEuiKbtuPerSqft"])
        assert block["intervalLow"] == pytest.approx(value - 1.5 * rmse)
        assert block["intervalHigh"] == pytest.approx(value + 1.5 * rmse)
