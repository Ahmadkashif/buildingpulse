"""Pillars for the success path of `POST /api/predictions`.

Validation failures live in `test_api_predictions_validation.py`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi.testclient import TestClient

from app.schemas import PredictionResponse


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
        before = datetime.now(timezone.utc)
        response = client.post("/api/predictions", json=valid_request_body)
        after = datetime.now(timezone.utc)

        raw = response.json()["data"]["generatedAt"]
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

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


class TestStubFieldsPassThrough:
    """Phase 1 invariant: prediction/peer/ll97 blocks equal the stub verbatim.

    Phase 4 will replace `prediction`; Phase 5 replaces `peer`; Phase 6 replaces
    `ll97`. These tests must be updated — not deleted — when each phase lands.
    """

    def test_prediction_block_equals_stub(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        from app.fixtures.stub_prediction import STUB  # type: ignore[attr-defined]

        response = client.post("/api/predictions", json=valid_request_body)
        assert response.json()["data"]["prediction"] == STUB["prediction"]

    def test_peer_block_equals_stub(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        from app.fixtures.stub_prediction import STUB  # type: ignore[attr-defined]

        response = client.post("/api/predictions", json=valid_request_body)
        assert response.json()["data"]["peer"] == STUB["peer"]

    def test_ll97_block_equals_stub(
        self, client: TestClient, valid_request_body: dict[str, Any]
    ) -> None:
        from app.fixtures.stub_prediction import STUB  # type: ignore[attr-defined]

        response = client.post("/api/predictions", json=valid_request_body)
        assert response.json()["data"]["ll97"] == STUB["ll97"]
