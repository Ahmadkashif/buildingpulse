"""Integration: `POST /api/predictions` writes exactly one audit row on success
and zero rows on validation failure.

The TestClient runs the real FastAPI app with its lifespan-applied migrations
against a temporary SQLite file pointed at by `DB_PATH`.
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


def _audit_rows(db_path: Path) -> list[tuple[Any, ...]]:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(
            "SELECT event_type, prediction_id, request_id, payload_json FROM audit_log ORDER BY id"
        ).fetchall()
    finally:
        conn.close()


VALID_BODY = {
    "propertyType": "office",
    "borough": "manhattan",
    "grossFloorAreaSqft": 50000,
    "yearBuilt": 2000,
    "numberOfBuildings": 1,
}


class TestSuccessfulPredictionWritesOneAuditRow:
    def test_one_row_written(self, client: TestClient, db_path: Path) -> None:
        response = client.post("/api/predictions", json=VALID_BODY)
        assert response.status_code == 201

        rows = _audit_rows(db_path)
        assert len(rows) == 1
        event_type, prediction_id, _request_id, _payload = rows[0]
        assert event_type == "prediction_generated"
        assert prediction_id == response.json()["data"]["id"]

    def test_request_id_matches_response_header(self, client: TestClient, db_path: Path) -> None:
        response = client.post("/api/predictions", json=VALID_BODY)
        assert response.status_code == 201

        header_request_id = response.headers["X-Request-ID"]
        rows = _audit_rows(db_path)
        assert len(rows) == 1
        assert rows[0][2] == header_request_id

    def test_two_calls_write_two_rows(self, client: TestClient, db_path: Path) -> None:
        client.post("/api/predictions", json=VALID_BODY)
        client.post("/api/predictions", json=VALID_BODY)
        assert len(_audit_rows(db_path)) == 2


class TestValidationFailureWritesNoAuditRow:
    def test_empty_body_returns_422_and_no_audit_row(
        self, client: TestClient, db_path: Path
    ) -> None:
        response = client.post("/api/predictions", json={})
        assert response.status_code == 422
        assert _audit_rows(db_path) == []

    def test_invalid_then_valid_only_writes_one_row(
        self, client: TestClient, db_path: Path
    ) -> None:
        bad = client.post("/api/predictions", json={})
        assert bad.status_code == 422
        good = client.post("/api/predictions", json=VALID_BODY)
        assert good.status_code == 201

        rows = _audit_rows(db_path)
        assert len(rows) == 1
        assert rows[0][1] == good.json()["data"]["id"]
