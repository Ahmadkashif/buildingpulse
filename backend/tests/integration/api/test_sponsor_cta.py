"""Integration: GET /api/sponsor/cta.

Pinned per issue #74:

1. 302 with Location carrying both UTM params + prediction_id +
   scenario_id (when supplied).
2. ``SponsorCtaFollowed`` audit row written *before* the redirect
   returns.
3. Missing ``prediction_id`` -> 422.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

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


class TestRedirect:
    def test_302_with_utm_and_ids(self, client: TestClient) -> None:
        response = client.get(
            "/api/sponsor/cta",
            params={"prediction_id": "pred_test", "scenario_id": "heat_pump"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        location = response.headers["location"]
        parts = urlsplit(location)
        assert f"{parts.scheme}://{parts.netloc}{parts.path}" == (
            "https://acme-energy.example.com/contact"
        )

        query = parse_qs(parts.query)
        assert query["prediction_id"] == ["pred_test"]
        assert query["scenario_id"] == ["heat_pump"]
        assert query["utm_source"] == ["buildingpulse"]
        assert query["utm_campaign"] == ["ll97_report"]

    def test_302_without_scenario_omits_scenario_param(self, client: TestClient) -> None:
        response = client.get(
            "/api/sponsor/cta",
            params={"prediction_id": "pred_only"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        query = parse_qs(urlsplit(response.headers["location"]).query)
        assert query["prediction_id"] == ["pred_only"]
        assert "scenario_id" not in query
        assert query["utm_source"] == ["buildingpulse"]
        assert query["utm_campaign"] == ["ll97_report"]


class TestAuditWrite:
    def test_audit_row_written_before_redirect(
        self, client: TestClient, db_path: Path
    ) -> None:
        response = client.get(
            "/api/sponsor/cta",
            params={"prediction_id": "pred_audit", "scenario_id": "envelope"},
            follow_redirects=False,
        )

        assert response.status_code == 302

        rows = _audit_rows(db_path)
        assert len(rows) == 1
        event_type, prediction_id, payload_json = rows[0]
        assert event_type == "sponsor_cta_followed"
        assert prediction_id == "pred_audit"
        payload = json.loads(payload_json)
        assert payload["scenario_id"] == "envelope"

    def test_audit_row_written_when_scenario_omitted(
        self, client: TestClient, db_path: Path
    ) -> None:
        response = client.get(
            "/api/sponsor/cta",
            params={"prediction_id": "pred_no_scenario"},
            follow_redirects=False,
        )

        assert response.status_code == 302
        rows = _audit_rows(db_path)
        assert len(rows) == 1
        event_type, prediction_id, payload_json = rows[0]
        assert event_type == "sponsor_cta_followed"
        assert prediction_id == "pred_no_scenario"
        assert json.loads(payload_json)["scenario_id"] is None


class TestValidation:
    def test_missing_prediction_id_returns_422(
        self, client: TestClient, db_path: Path
    ) -> None:
        response = client.get("/api/sponsor/cta", follow_redirects=False)

        assert response.status_code == 422
        assert _audit_rows(db_path) == []

    def test_blank_prediction_id_returns_422(
        self, client: TestClient, db_path: Path
    ) -> None:
        response = client.get(
            "/api/sponsor/cta",
            params={"prediction_id": ""},
            follow_redirects=False,
        )

        assert response.status_code == 422
        assert _audit_rows(db_path) == []
