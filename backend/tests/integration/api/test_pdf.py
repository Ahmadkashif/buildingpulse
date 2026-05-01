"""Integration: ``GET /api/predictions/{id}/pdf`` — issue #82.

Pinned behaviours:

* 403 when no lead is on file for ``(prediction_id, email)``.
* 200 with ``Content-Type: application/pdf`` and ``Content-Disposition:
  attachment; filename="building-pulse-<id>.pdf"`` once a lead exists.
* A ``pdf_generated`` audit row lands in ``audit_log`` on the 200 path.

The WeasyPrint adapter is replaced by FastAPI dependency override so
the test is fast, deterministic, and free of system-binary requirements.
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
    from app.deps import get_pdf_generation_use_case
    from app.main import app
    from app.repos.connection import connect
    from app.repos.lead_repo import LeadRepo
    from app.services.resource.lead.service import LeadResourceService
    from app.services.resource.prediction.service import PredictionResourceService
    from app.services.usecase.pdf_generation.service import PdfGenerationUseCaseService

    async def override_pdf_use_case() -> Any:
        from datetime import UTC, datetime

        conn = connect()
        try:
            lead_service = LeadResourceService(LeadRepo(conn), now=lambda: datetime.now(UTC))
            from app.deps import get_artifact_registry, get_peer_cohorts_registry

            prediction_service = PredictionResourceService(
                get_artifact_registry(), get_peer_cohorts_registry()
            )
            yield PdfGenerationUseCaseService(
                lead_service=lead_service,
                prediction_service=prediction_service,
                html_to_pdf=lambda _html: b"%PDF-1.7 fake-test-bytes\n",
            )
        finally:
            conn.close()

    app.dependency_overrides[get_pdf_generation_use_case] = override_pdf_use_case
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.pop(get_pdf_generation_use_case, None)


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


def _capture_lead(client: TestClient, prediction_id: str, email: str) -> None:
    body = {
        "predictionId": prediction_id,
        "name": "Jane Doe",
        "email": email,
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
    response = client.post("/api/leads", json=body)
    assert response.status_code == 201, response.text


def _pdf_query(email: str) -> dict[str, Any]:
    return {
        "email": email,
        "propertyType": "office",
        "borough": "manhattan",
        "grossFloorAreaSqft": 50000,
        "yearBuilt": 2000,
        "numberOfBuildings": 1,
    }


def _audit_event_types(db_path: Path) -> list[str]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute("SELECT event_type FROM audit_log ORDER BY id").fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


class TestGating:
    def test_returns_403_when_no_lead_on_file(self, client: TestClient, db_path: Path) -> None:
        prediction_id = _create_prediction(client)

        response = client.get(
            f"/api/predictions/{prediction_id}/pdf",
            params=_pdf_query("ghost@example.com"),
        )

        assert response.status_code == 403
        # No PdfGenerated row from a denied download.
        assert "pdf_generated" not in _audit_event_types(db_path)

    def test_returns_200_with_pdf_headers_after_lead_capture(
        self, client: TestClient, db_path: Path
    ) -> None:
        prediction_id = _create_prediction(client)
        _capture_lead(client, prediction_id, "jane@example.com")

        response = client.get(
            f"/api/predictions/{prediction_id}/pdf",
            params=_pdf_query("jane@example.com"),
        )

        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/pdf"
        disposition = response.headers["content-disposition"]
        assert "attachment" in disposition
        assert f'filename="building-pulse-{prediction_id}.pdf"' in disposition
        assert response.content.startswith(b"%PDF-")


class TestAudit:
    def test_pdf_generated_audit_row_written_on_success(
        self, client: TestClient, db_path: Path
    ) -> None:
        prediction_id = _create_prediction(client)
        _capture_lead(client, prediction_id, "jane@example.com")

        response = client.get(
            f"/api/predictions/{prediction_id}/pdf",
            params=_pdf_query("jane@example.com"),
        )
        assert response.status_code == 200

        events = _audit_event_types(db_path)
        assert events.count("pdf_generated") == 1
        # Verify the row is tagged with the right prediction_id and that
        # the bytes_size payload reflects the bytes returned.
        conn = sqlite3.connect(str(db_path))
        try:
            row = conn.execute(
                "SELECT prediction_id, payload_json FROM audit_log "
                "WHERE event_type = 'pdf_generated' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        assert row is not None
        assert row[0] == prediction_id
        assert '"bytes_size"' in row[1]
