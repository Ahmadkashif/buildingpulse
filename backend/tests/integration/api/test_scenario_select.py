"""Integration: ``POST /api/scenarios/{scenario_id}/select``.

Pinned per issue #79:

1. Happy path: 200 + a single ``scenario_selected`` audit row that
   carries the prediction id (top-level) and scenario id (in payload).
2. Unknown scenario id -> 404, no audit row written.
3. Unknown prediction id (does not match the ``pred_<hex>`` shape) -> 404.
4. Idempotency: a second call within the dedupe window does not write a
   second row; the response advertises ``deduped: true``.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from app.policy.retrofits import LIBRARY
from fastapi.testclient import TestClient


KNOWN_SCENARIO_ID = next(s.id for s in LIBRARY["office"])


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


def _audit_rows(db_path: Path) -> list[tuple[str, str | None, str]]:
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT event_type, prediction_id, payload_json "
            "FROM audit_log ORDER BY id"
        ).fetchall()
        return [(r[0], r[1], r[2]) for r in rows]
    finally:
        conn.close()


class TestHappyPath:
    def test_records_scenario_selected_and_returns_200(
        self, client: TestClient, db_path: Path
    ) -> None:
        response = client.post(
            f"/api/scenarios/{KNOWN_SCENARIO_ID}/select",
            json={"predictionId": "pred_abc123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["predictionId"] == "pred_abc123"
        assert body["data"]["scenarioId"] == KNOWN_SCENARIO_ID
        assert body["data"]["deduped"] is False

        rows = _audit_rows(db_path)
        assert len(rows) == 1
        event_type, prediction_id, payload_json = rows[0]
        assert event_type == "scenario_selected"
        assert prediction_id == "pred_abc123"
        assert json.loads(payload_json)["scenario_id"] == KNOWN_SCENARIO_ID


class TestUnknownIds:
    def test_unknown_scenario_id_returns_404(
        self, client: TestClient, db_path: Path
    ) -> None:
        response = client.post(
            "/api/scenarios/not-a-real-scenario/select",
            json={"predictionId": "pred_abc123"},
        )
        assert response.status_code == 404
        assert _audit_rows(db_path) == []

    def test_unknown_prediction_id_returns_404(
        self, client: TestClient, db_path: Path
    ) -> None:
        response = client.post(
            f"/api/scenarios/{KNOWN_SCENARIO_ID}/select",
            json={"predictionId": "not-a-real-id"},
        )
        assert response.status_code == 404
        assert _audit_rows(db_path) == []

    def test_blank_prediction_id_returns_422(
        self, client: TestClient, db_path: Path
    ) -> None:
        response = client.post(
            f"/api/scenarios/{KNOWN_SCENARIO_ID}/select",
            json={"predictionId": ""},
        )
        assert response.status_code == 422
        assert _audit_rows(db_path) == []


class TestIdempotency:
    def test_rapid_duplicate_records_only_one_row(
        self, client: TestClient, db_path: Path
    ) -> None:
        first = client.post(
            f"/api/scenarios/{KNOWN_SCENARIO_ID}/select",
            json={"predictionId": "pred_dup"},
        )
        second = client.post(
            f"/api/scenarios/{KNOWN_SCENARIO_ID}/select",
            json={"predictionId": "pred_dup"},
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["data"]["deduped"] is False
        assert second.json()["data"]["deduped"] is True

        rows = _audit_rows(db_path)
        assert len(rows) == 1

    def test_different_scenario_ids_are_not_deduped(
        self, client: TestClient, db_path: Path
    ) -> None:
        scenarios = [s.id for s in LIBRARY["office"]]
        assert len(scenarios) >= 2
        a = client.post(
            f"/api/scenarios/{scenarios[0]}/select",
            json={"predictionId": "pred_two"},
        )
        b = client.post(
            f"/api/scenarios/{scenarios[1]}/select",
            json={"predictionId": "pred_two"},
        )
        assert a.status_code == 200
        assert b.status_code == 200
        rows = _audit_rows(db_path)
        assert len(rows) == 2
