"""Integration: ``POST /api/leads``.

Pinned behaviours per issue #71 acceptance criteria:

* 201 on first capture, 200 on the within-window idempotent repeat.
* 422 on missing consent / invalid email / invalid phone format.
* 404 when ``prediction_id`` is unknown (no ``prediction_generated``
  audit row).
* Response body is a fixed envelope ``{"data": {"id": "<lead_id>"}}``.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "buildingpulse.db"
    monkeypatch.setenv("DB_PATH", str(path))
    return path


@pytest.fixture
def client(db_path: Path) -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as c:
        yield c


VALID_PREDICTION_BODY = {
    "propertyType": "office",
    "borough": "manhattan",
    "grossFloorAreaSqft": 50000,
    "yearBuilt": 2000,
    "numberOfBuildings": 1,
}


def _create_prediction(client: TestClient) -> str:
    response = client.post("/api/predictions", json=VALID_PREDICTION_BODY)
    assert response.status_code == 201, response.text
    return str(response.json()["data"]["id"])


def _lead_body(prediction_id: str, **overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "predictionId": prediction_id,
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0100",
        "role": "owner",
        "consentGiven": True,
        "scenarioId": None,
        "propertyType": "office",
        "borough": "manhattan",
        "grossFloorAreaSqft": 50000,
        "yearBuilt": 2000,
        "predictedEui": 87.3,
        "projectedFineUsd": 12345.0,
        "atRisk": True,
        "reportUrl": f"https://buildingpulse.example.com/r/{prediction_id}",
    }
    body.update(overrides)
    return body


def _leads_rows(db_path: Path) -> list[tuple[Any, ...]]:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(
            "SELECT id, prediction_id, email, name FROM leads ORDER BY created_at"
        ).fetchall()
    finally:
        conn.close()


def _audit_event_types(db_path: Path) -> list[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT event_type FROM audit_log ORDER BY id").fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


class TestHappyPath:
    def test_first_capture_returns_201_with_lead_id(
        self, client: TestClient, db_path: Path
    ) -> None:
        prediction_id = _create_prediction(client)

        response = client.post("/api/leads", json=_lead_body(prediction_id))

        assert response.status_code == 201
        body = response.json()
        assert set(body.keys()) == {"data"}
        assert set(body["data"].keys()) == {"id"}
        lead_id = body["data"]["id"]
        assert isinstance(lead_id, str)
        assert lead_id

        rows = _leads_rows(db_path)
        assert len(rows) == 1
        assert rows[0][0] == lead_id
        assert rows[0][1] == prediction_id
        assert rows[0][2] == "jane@example.com"

    def test_idempotent_repeat_returns_200_with_same_lead_id(
        self, client: TestClient, db_path: Path
    ) -> None:
        prediction_id = _create_prediction(client)

        first = client.post("/api/leads", json=_lead_body(prediction_id))
        assert first.status_code == 201
        first_id = first.json()["data"]["id"]

        second = client.post("/api/leads", json=_lead_body(prediction_id, name="Jane R. Doe"))
        assert second.status_code == 200
        assert second.json()["data"]["id"] == first_id

        rows = _leads_rows(db_path)
        assert len(rows) == 1
        assert rows[0][3] == "Jane R. Doe"

        events = _audit_event_types(db_path)
        # 1x prediction_generated, 2x lead_captured, 1x partner_notification_dispatched.
        assert events.count("lead_captured") == 2
        assert events.count("partner_notification_dispatched") == 1


class TestValidationErrors:
    def test_missing_consent_returns_422(self, client: TestClient) -> None:
        prediction_id = _create_prediction(client)
        body = _lead_body(prediction_id)
        del body["consentGiven"]

        response = client.post("/api/leads", json=body)
        assert response.status_code == 422

    def test_consent_false_returns_422(self, client: TestClient) -> None:
        prediction_id = _create_prediction(client)
        response = client.post("/api/leads", json=_lead_body(prediction_id, consentGiven=False))
        assert response.status_code == 422

    def test_invalid_email_returns_422(self, client: TestClient) -> None:
        prediction_id = _create_prediction(client)
        response = client.post("/api/leads", json=_lead_body(prediction_id, email="not-an-email"))
        assert response.status_code == 422

    def test_invalid_phone_returns_422(self, client: TestClient) -> None:
        prediction_id = _create_prediction(client)
        response = client.post("/api/leads", json=_lead_body(prediction_id, phone="abc"))
        assert response.status_code == 422


class TestUnknownPrediction:
    def test_unknown_prediction_id_returns_404(self, client: TestClient, db_path: Path) -> None:
        response = client.post("/api/leads", json=_lead_body("pred_does_not_exist"))
        assert response.status_code == 404
        assert _leads_rows(db_path) == []
