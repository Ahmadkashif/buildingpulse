"""Shared fixtures for Phase 1 tests.

The Contract (see MVP_PLAN.md) is the single source of truth for the shapes
below. These fixtures exist so every test references the same canonical
example, not a per-test ad-hoc dict.
"""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture
def valid_request_body() -> dict[str, Any]:
    """The canonical valid `POST /api/predictions` request body."""
    return {
        "propertyType": "multifamily-housing",
        "borough": "brooklyn",
        "grossFloorAreaSqft": 45000,
        "yearBuilt": 1925,
        "numberOfBuildings": 1,
    }


@pytest.fixture
def valid_response_body() -> dict[str, Any]:
    """The canonical valid `PredictionResponse` example from the Contract."""
    return {
        "id": "pred_sample_01",
        "generatedAt": "2026-04-16T14:30:00-04:00",
        "input": {
            "propertyType": "multifamily-housing",
            "borough": "brooklyn",
            "grossFloorAreaSqft": 45000,
            "yearBuilt": 1925,
            "numberOfBuildings": 1,
        },
        "prediction": {
            "siteEuiKbtuPerSqft": 87.3,
            "intervalLow": 65.2,
            "intervalHigh": 109.4,
            "modelVersion": "baseline-lr-v1",
        },
        "peer": {
            "cohort": {
                "propertyType": "multifamily-housing",
                "borough": "brooklyn",
                "ageBand": "pre-1950",
            },
            "cohortSize": 1420,
            "medianSiteEui": 74.1,
            "p25SiteEui": 58.0,
            "p75SiteEui": 94.5,
            "percentile": 68,
        },
        "ll97": {
            "capKbtuPerSqft2024To2029": 6.75,
            "capKbtuPerSqft2030To2034": 4.53,
            "projectedAnnualFineUsd2024": 0,
            "projectedAnnualFineUsd2030": 12400,
            "atRisk": True,
            "fineSeries": [
                {"year": 2026, "projectedAnnualFineUsd": 0},
                {"year": 2027, "projectedAnnualFineUsd": 0},
                {"year": 2028, "projectedAnnualFineUsd": 0},
                {"year": 2029, "projectedAnnualFineUsd": 0},
                {"year": 2030, "projectedAnnualFineUsd": 12400},
                {"year": 2031, "projectedAnnualFineUsd": 12400},
                {"year": 2032, "projectedAnnualFineUsd": 12400},
                {"year": 2033, "projectedAnnualFineUsd": 12400},
                {"year": 2034, "projectedAnnualFineUsd": 12400},
            ],
        },
    }


SPONSOR_ENV_DEFAULTS: dict[str, str] = {
    "SPONSOR_ID": "acme-energy",
    "SPONSOR_NAME": "Acme Energy",
    "SPONSOR_LOGO_URL": "https://cdn.example.com/acme-logo.svg",
    "SPONSOR_CTA_LABEL": "Talk to a contractor",
    "SPONSOR_CTA_URL": "https://acme-energy.example.com/contact",
    "SPONSOR_LEAD_EMAIL": "leads@acme-energy.example.com",
}


@pytest.fixture(autouse=True)
def _sponsor_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide sponsor env-var defaults so the FastAPI lifespan can boot.

    Missing-env failure tests can override with `monkeypatch.delenv(...)`
    before constructing the app.
    """
    for var, value in SPONSOR_ENV_DEFAULTS.items():
        monkeypatch.setenv(var, value)
    monkeypatch.delenv("SPONSOR_LEAD_WEBHOOK_URL", raising=False)
    # Reset the AppConfig singleton between tests so env-var changes inside
    # a test take effect when the next FastAPI lifespan boots.
    from app.deps import _reset_app_config

    _reset_app_config()


@pytest.fixture
def client(tmp_path: Any, monkeypatch: pytest.MonkeyPatch) -> Any:
    """FastAPI TestClient with a per-test SQLite DB and lifespan-applied migrations."""
    from app.main import app  # type: ignore[attr-defined]
    from fastapi.testclient import TestClient

    monkeypatch.setenv("DB_PATH", str(tmp_path / "buildingpulse.db"))
    with TestClient(app) as c:
        yield c
