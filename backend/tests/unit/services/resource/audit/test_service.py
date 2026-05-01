"""Unit tests for AuditService — branch-coverage 100% target.

The repo is faked; these tests pin the column-vs-payload split, the
event_type discriminator, and the JSON serialization of payload fields.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import pytest
from app.domain.audit.types import (
    AuditEvent,
    LeadCaptured,
    PartnerNotificationDispatched,
    PartnerNotificationFailed,
    PdfGenerated,
    PredictionGenerated,
    ScenarioSelected,
    SponsorCtaFollowed,
)
from app.services.resource.audit.service import AuditService


@dataclass
class FakeAuditRepo:
    rows: list[dict[str, Any]] = field(default_factory=list)
    next_id: int = 1

    def insert(
        self,
        *,
        event_type: str,
        occurred_at: str,
        request_id: str,
        trace_id: str,
        prediction_id: str | None,
        lead_id: str | None,
        actor_session_id: str,
        payload_json: str,
    ) -> int:
        self.rows.append(
            {
                "event_type": event_type,
                "occurred_at": occurred_at,
                "request_id": request_id,
                "trace_id": trace_id,
                "prediction_id": prediction_id,
                "lead_id": lead_id,
                "actor_session_id": actor_session_id,
                "payload_json": payload_json,
            }
        )
        rid = self.next_id
        self.next_id += 1
        return rid


_OCCURRED_AT = datetime(2026, 5, 1, 10, 30, 0, tzinfo=UTC)
_COMMON = {
    "occurred_at": _OCCURRED_AT,
    "request_id": "req_123",
    "trace_id": "trace_abc",
    "actor_session_id": "sess_xyz",
}


@pytest.fixture
def repo() -> FakeAuditRepo:
    return FakeAuditRepo()


@pytest.fixture
def service(repo: FakeAuditRepo) -> AuditService:
    return AuditService(repo)  # type: ignore[arg-type]


async def test_record_returns_repo_lastrowid(service: AuditService, repo: FakeAuditRepo) -> None:
    repo.next_id = 42
    event = ScenarioSelected(**_COMMON, prediction_id="p1", scenario_id="s1")
    rid = await service.record(event)
    assert rid == 42


async def test_record_persists_top_level_columns(
    service: AuditService, repo: FakeAuditRepo
) -> None:
    event = PredictionGenerated(
        **_COMMON,
        prediction_id="pred_1",
        model_version="v1",
        site_eui_kbtu_per_sqft=87.3,
    )
    await service.record(event)
    [row] = repo.rows
    assert row["event_type"] == "prediction_generated"
    assert row["occurred_at"] == _OCCURRED_AT.isoformat()
    assert row["request_id"] == "req_123"
    assert row["trace_id"] == "trace_abc"
    assert row["actor_session_id"] == "sess_xyz"
    assert row["prediction_id"] == "pred_1"
    assert row["lead_id"] is None


async def test_payload_json_strips_common_columns(
    service: AuditService, repo: FakeAuditRepo
) -> None:
    event = PredictionGenerated(
        **_COMMON,
        model_version="baseline-lr-v1",
        site_eui_kbtu_per_sqft=87.3,
    )
    await service.record(event)
    payload = json.loads(repo.rows[0]["payload_json"])
    assert payload == {
        "model_version": "baseline-lr-v1",
        "site_eui_kbtu_per_sqft": 87.3,
    }
    for column in (
        "event_type",
        "occurred_at",
        "request_id",
        "trace_id",
        "actor_session_id",
        "prediction_id",
        "lead_id",
    ):
        assert column not in payload


async def test_lead_captured_carries_lead_id_and_pii_in_payload(
    service: AuditService, repo: FakeAuditRepo
) -> None:
    event = LeadCaptured(
        **_COMMON,
        prediction_id="pred_1",
        lead_id="lead_1",
        email="user@example.com",
        consent_given_at=_OCCURRED_AT,
    )
    await service.record(event)
    row = repo.rows[0]
    assert row["lead_id"] == "lead_1"
    payload = json.loads(row["payload_json"])
    assert payload["email"] == "user@example.com"
    consent = payload["consent_given_at"].replace("Z", "+00:00")
    assert datetime.fromisoformat(consent) == _OCCURRED_AT
    # payload_json keys are sorted alphabetically — `consent_given_at` precedes
    # `email` despite being declared second on the model. This is the contract
    # downstream log readers depend on for stable diffing.
    consent_pos = row["payload_json"].index('"consent_given_at"')
    email_pos = row["payload_json"].index('"email"')
    assert consent_pos < email_pos


async def test_partner_notification_dispatched(service: AuditService, repo: FakeAuditRepo) -> None:
    event = PartnerNotificationDispatched(**_COMMON, lead_id="lead_1", channel="email")
    await service.record(event)
    row = repo.rows[0]
    assert row["event_type"] == "partner_notification_dispatched"
    assert json.loads(row["payload_json"]) == {"channel": "email"}


async def test_partner_notification_failed(service: AuditService, repo: FakeAuditRepo) -> None:
    event = PartnerNotificationFailed(
        **_COMMON, lead_id="lead_1", channel="email", reason="smtp_timeout"
    )
    await service.record(event)
    row = repo.rows[0]
    assert row["event_type"] == "partner_notification_failed"
    assert json.loads(row["payload_json"]) == {
        "channel": "email",
        "reason": "smtp_timeout",
    }


async def test_pdf_generated(service: AuditService, repo: FakeAuditRepo) -> None:
    event = PdfGenerated(**_COMMON, prediction_id="pred_1", bytes_size=12345)
    await service.record(event)
    assert repo.rows[0]["event_type"] == "pdf_generated"
    assert json.loads(repo.rows[0]["payload_json"]) == {"bytes_size": 12345}


async def test_sponsor_cta_followed_with_scenario(
    service: AuditService, repo: FakeAuditRepo
) -> None:
    event = SponsorCtaFollowed(**_COMMON, prediction_id="pred_1", scenario_id="scen_1")
    await service.record(event)
    assert json.loads(repo.rows[0]["payload_json"]) == {"scenario_id": "scen_1"}


async def test_sponsor_cta_followed_without_scenario(
    service: AuditService, repo: FakeAuditRepo
) -> None:
    event = SponsorCtaFollowed(**_COMMON, prediction_id="pred_1")
    await service.record(event)
    assert json.loads(repo.rows[0]["payload_json"]) == {"scenario_id": None}


async def test_match_on_event_type_is_exhaustive(
    service: AuditService, repo: FakeAuditRepo
) -> None:
    """Exercises every discriminator branch via a `match` to lock in
    that the union covers all seven cases."""

    events: list[AuditEvent] = [
        PredictionGenerated(**_COMMON, model_version="v", site_eui_kbtu_per_sqft=1.0),
        LeadCaptured(**_COMMON, lead_id="l", email="a@b.c", consent_given_at=_OCCURRED_AT),
        PartnerNotificationDispatched(**_COMMON, channel="email"),
        PartnerNotificationFailed(**_COMMON, channel="email", reason="x"),
        ScenarioSelected(**_COMMON, scenario_id="s"),
        PdfGenerated(**_COMMON, bytes_size=1),
        SponsorCtaFollowed(**_COMMON),
    ]
    seen: set[str] = set()
    for ev in events:
        match ev:
            case PredictionGenerated():
                seen.add("prediction_generated")
            case LeadCaptured():
                seen.add("lead_captured")
            case PartnerNotificationDispatched():
                seen.add("partner_notification_dispatched")
            case PartnerNotificationFailed():
                seen.add("partner_notification_failed")
            case ScenarioSelected():
                seen.add("scenario_selected")
            case PdfGenerated():
                seen.add("pdf_generated")
            case SponsorCtaFollowed():
                seen.add("sponsor_cta_followed")
        await service.record(ev)
    assert seen == {
        "prediction_generated",
        "lead_captured",
        "partner_notification_dispatched",
        "partner_notification_failed",
        "scenario_selected",
        "pdf_generated",
        "sponsor_cta_followed",
    }
    assert len(repo.rows) == 7
