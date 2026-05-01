"""Integration: GET /api/address/lookup.

Pinned per issue #87:

1. Flag default off: every call returns 404, even with a known address.
2. Flag on, known address: 200 with the matched record (camelCase).
3. Flag on, unknown address: 404.
4. Flag on, missing/blank query param: 422.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "buildingpulse.db"
    monkeypatch.setenv("DB_PATH", str(path))
    return path


def _new_client(db_path: Path) -> Iterator[TestClient]:
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_flag_off(db_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.delenv("ADDRESS_LOOKUP_ENABLED", raising=False)
    yield from _new_client(db_path)


@pytest.fixture
def client_flag_on(db_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("ADDRESS_LOOKUP_ENABLED", "true")
    yield from _new_client(db_path)


# A known address present in the committed LL84 index parquet artifact.
# The synthetic dataset uses ``"<n> SYNTH ST"`` for addresses; ``100 SYNTH ST``
# is the first row (see ``training.build_ll84_index._synthetic_address``).
KNOWN_ADDRESS = "100 SYNTH ST"


class TestFlagOff:
    def test_default_returns_404(self, client_flag_off: TestClient) -> None:
        response = client_flag_off.get("/api/address/lookup", params={"address": KNOWN_ADDRESS})
        assert response.status_code == 404

    def test_flag_off_ignores_missing_param(self, client_flag_off: TestClient) -> None:
        response = client_flag_off.get("/api/address/lookup")
        assert response.status_code == 404


class TestFlagOnHappyPath:
    def test_returns_200_with_matched_record(self, client_flag_on: TestClient) -> None:
        response = client_flag_on.get("/api/address/lookup", params={"address": KNOWN_ADDRESS})
        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"data"}
        data = body["data"]
        assert data["addressNormalized"] == "100 SYNTH ST"
        assert data["confidence"] in {"high", "low"}
        assert "bbl" in data
        assert "propertyType" in data
        assert "borough" in data
        assert "grossFloorAreaSqft" in data
        assert "yearBuilt" in data
        assert "numberOfBuildings" in data

    def test_fuzzy_match_still_returns_200(self, client_flag_on: TestClient) -> None:
        # A near-miss with the same house number should fuzz to the
        # known record (low or high confidence both acceptable).
        response = client_flag_on.get("/api/address/lookup", params={"address": "100 synth street"})
        assert response.status_code == 200
        assert response.json()["data"]["addressNormalized"] == "100 SYNTH ST"


class TestFlagOnMiss:
    def test_unknown_address_returns_404(self, client_flag_on: TestClient) -> None:
        response = client_flag_on.get(
            "/api/address/lookup",
            params={"address": "9999 NOWHERE BOULEVARD UNINDEXED"},
        )
        assert response.status_code == 404


class TestFlagOnValidation:
    def test_missing_address_returns_422(self, client_flag_on: TestClient) -> None:
        response = client_flag_on.get("/api/address/lookup")
        assert response.status_code == 422

    def test_blank_address_returns_422(self, client_flag_on: TestClient) -> None:
        response = client_flag_on.get("/api/address/lookup", params={"address": "   "})
        assert response.status_code == 422
