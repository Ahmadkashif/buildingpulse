"""Integration: GET /api/sponsor.

Three behaviors are pinned here:

1. Happy path returns 200 with the five public display fields.
2. Lead-routing fields (email, webhook) are NEVER serialized.
3. A missing required sponsor env var fails at startup (lifespan), not on
   the first request — the FastAPI app refuses to come up at all.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from app.config import ConfigError
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


class TestSponsorEndpointHappyPath:
    def test_returns_200_with_five_public_fields(self, client: TestClient) -> None:
        response = client.get("/api/sponsor")

        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"data"}

        data = body["data"]
        assert set(data.keys()) == {"id", "name", "logoUrl", "ctaLabel", "ctaUrl"}
        assert data["id"] == "acme-energy"
        assert data["name"] == "Acme Energy"
        assert data["logoUrl"] == "https://cdn.example.com/acme-logo.svg"
        assert data["ctaLabel"] == "Talk to a contractor"
        assert data["ctaUrl"] == "https://acme-energy.example.com/contact"

    def test_lead_routing_fields_not_exposed(self, client: TestClient) -> None:
        response = client.get("/api/sponsor")
        assert response.status_code == 200

        data = response.json()["data"]
        # Acceptance criterion: GET /api/sponsor MUST NOT leak the lead
        # destination fields to the public.
        assert "leadEmail" not in data
        assert "leadWebhookUrl" not in data
        assert "lead_email" not in data
        assert "lead_webhook_url" not in data

        raw = response.text
        assert "leads@acme-energy.example.com" not in raw


class TestSponsorEndpointMissingEnv:
    def test_missing_sponsor_name_fails_at_startup(
        self, db_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SPONSOR_NAME", raising=False)

        from app.main import app

        # The failure must happen during lifespan startup, before any
        # request is dispatched. Entering the TestClient context manager
        # runs the lifespan hook.
        with pytest.raises(ConfigError) as excinfo, TestClient(app):
            pass

        assert "SPONSOR_NAME" in str(excinfo.value)

    def test_missing_sponsor_lead_email_fails_at_startup(
        self, db_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SPONSOR_LEAD_EMAIL", raising=False)

        from app.main import app

        with pytest.raises(ConfigError) as excinfo, TestClient(app):
            pass

        assert "SPONSOR_LEAD_EMAIL" in str(excinfo.value)
