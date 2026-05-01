"""Integration: ``POST /api/predictions`` returns a real ``peer`` block.

Two paths are exercised end-to-end through the live FastAPI app:

* **Narrow** — the ``(property_type, borough, age_band)`` cohort has
  enough rows; the response echoes a fully-populated cohort.
* **Fallback** — the narrow cohort is too small; the lookup widens, and
  the response's ``peer.cohort`` carries ``null`` on the dropped axis
  (``borough`` and/or ``ageBand``).

The narrow case runs against the real artifacts. The fallback case
overrides the peer-cohorts dependency with a sparse synthetic frame so
the broaden rule is forced to fire — that's the only deterministic way
to test fallback without depending on a hand-tuned production cohort.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest
from app.deps import get_artifact_registry, get_prediction_service
from app.repos.peer_cohorts_registry import PeerCohortsRegistry
from app.services.resource.prediction.service import PredictionResourceService
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


class TestNarrowCohortPath:
    """The real artifacts contain dense cohorts; the narrow path fires."""

    def test_peer_block_carries_real_percentile_and_summary(
        self, client: TestClient
    ) -> None:
        response = client.post("/api/predictions", json=VALID_BODY)
        assert response.status_code == 201
        peer = response.json()["data"]["peer"]

        assert isinstance(peer["percentile"], int)
        assert 0 <= peer["percentile"] <= 100
        assert peer["cohortSize"] >= 30
        assert peer["p25SiteEui"] <= peer["medianSiteEui"] <= peer["p75SiteEui"]

    def test_narrow_cohort_echoes_request_axes(self, client: TestClient) -> None:
        response = client.post("/api/predictions", json=VALID_BODY)
        peer = response.json()["data"]["peer"]
        cohort = peer["cohort"]
        # year_built=1985 → age band "1980-1999".
        assert cohort["propertyType"] == "office"
        assert cohort["borough"] == "manhattan"
        assert cohort["ageBand"] == "1980-1999"

    def test_percentile_shifts_monotonically_with_year_built(
        self, client: TestClient
    ) -> None:
        """Older + younger buildings select different age-band cohorts; the
        predicted EUI ranks differently inside each."""
        very_old = client.post(
            "/api/predictions", json={**VALID_BODY, "yearBuilt": 1900}
        ).json()["data"]["peer"]["percentile"]
        very_new = client.post(
            "/api/predictions", json={**VALID_BODY, "yearBuilt": 2024}
        ).json()["data"]["peer"]["percentile"]
        # Different cohorts produce different percentile ranks; this check
        # is the integration analogue of the curl self-verification step.
        assert very_old != very_new


def _sparse_cohorts_frame() -> pd.DataFrame:
    """A frame whose office/manhattan/1980-1999 cohort is below threshold."""
    rows: list[dict[str, object]] = []

    def add(prop: str, borough: str, age: str, count: int, base: float) -> None:
        eui = [base + float(i) for i in range(count)]
        rows.append(
            {
                "property_type": prop,
                "borough": borough,
                "age_band": age,
                "cohort_size": len(eui),
                "p25": float(np.percentile(eui, 25)) if eui else 0.0,
                "median": float(np.percentile(eui, 50)) if eui else 0.0,
                "p75": float(np.percentile(eui, 75)) if eui else 0.0,
                "eui_sorted": eui,
            }
        )

    # Narrow cohort: 5 rows — below MIN_COHORT_SIZE (30).
    add("office", "manhattan", "1980-1999", 5, 50.0)
    # Other boroughs in the same age band push the L2 cohort over 30.
    add("office", "bronx", "1980-1999", 20, 60.0)
    add("office", "brooklyn", "1980-1999", 20, 70.0)
    return pd.DataFrame(rows)


class _StubPeerCohortsRegistry(PeerCohortsRegistry):
    """In-memory PeerCohortsRegistry that skips the parquet read."""

    def __init__(self, frame: pd.DataFrame) -> None:
        self._cohorts = frame


class TestFallbackCohortPath:
    """A sparse synthetic cohort frame forces the broaden rule to fire."""

    def test_fallback_sets_borough_to_null_in_response(
        self, client: TestClient
    ) -> None:
        from app.main import app

        sparse = _StubPeerCohortsRegistry(_sparse_cohorts_frame())

        def _override() -> PredictionResourceService:
            return PredictionResourceService(get_artifact_registry(), sparse)

        app.dependency_overrides[get_prediction_service] = _override
        try:
            response = client.post("/api/predictions", json=VALID_BODY)
        finally:
            app.dependency_overrides.pop(get_prediction_service, None)

        assert response.status_code == 201
        peer = response.json()["data"]["peer"]
        cohort = peer["cohort"]
        assert cohort["propertyType"] == "office"
        # Fallback widened away from borough; age_band stays narrow.
        assert cohort["borough"] is None
        assert cohort["ageBand"] == "1980-1999"
        # Cohort size reflects the merged L2 frame: 5 + 20 + 20 = 45.
        assert peer["cohortSize"] == 45
