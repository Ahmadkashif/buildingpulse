"""Unit tests for :class:`LeadCaptureUseCaseService` — issue #70.

Pinned behaviours per the issue acceptance criteria:

* Composes exactly the three resource services (lead, notification,
  audit). The seam is the resource layer — fakes are substituted there,
  never one level deeper at a repo or integration.
* Audit always fires :class:`LeadCaptured`, even on the within-window
  re-submission case where partner notification is suppressed.
* Notification dispatch outcome translates 1:1 into the matching audit
  event:
  :class:`Dispatched` → :class:`PartnerNotificationDispatched`,
  :class:`Failed` → :class:`PartnerNotificationFailed`.
* Within the idempotency window: notification is **not** re-fired, but
  :class:`LeadCaptured` is — the audit log records the attempt.

Self-verification target: 100% branch coverage on the use-case module
under ``pytest --cov-branch``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from app.domain.audit.types import (
    LeadCaptured,
    PartnerNotificationDispatched,
    PartnerNotificationFailed,
)
from app.domain.lead import Lead
from app.domain.notification import (
    Dispatched,
    DispatchResult,
    Failed,
    LeadNotificationPayload,
)
from app.services.resource.lead.service import CaptureOutcome
from app.services.resource.notification.service import NotificationDispatchOutcome
from app.services.usecase.lead_capture.service import (
    LeadCaptureRequest,
    LeadCaptureResult,
    LeadCaptureUseCaseService,
)


# ---------------------------------------------------------------------------
# Fakes for each of the three resource services.
# ---------------------------------------------------------------------------


@dataclass
class FakeLeadResourceService:
    """Records inputs and returns a scripted :class:`CaptureOutcome` per call."""

    outcomes: list[CaptureOutcome]
    capture_calls: list[dict[str, Any]] = field(default_factory=list)

    def capture(self, **kwargs: Any) -> CaptureOutcome:
        self.capture_calls.append(kwargs)
        if not self.outcomes:
            raise AssertionError("FakeLeadResourceService: no scripted outcomes left")
        return self.outcomes.pop(0)


@dataclass
class FakeNotificationResourceService:
    """Records each ``notify`` call's payload and returns a scripted outcome."""

    outcomes: list[NotificationDispatchOutcome]
    notify_calls: list[LeadNotificationPayload] = field(default_factory=list)

    def notify(self, payload: LeadNotificationPayload) -> NotificationDispatchOutcome:
        self.notify_calls.append(payload)
        if not self.outcomes:
            raise AssertionError(
                "FakeNotificationResourceService: no scripted outcomes left"
            )
        return self.outcomes.pop(0)


@dataclass
class FakeAuditService:
    """Captures the AuditEvent objects passed to ``record`` in order."""

    events: list[Any] = field(default_factory=list)

    async def record(self, event: Any) -> int:
        self.events.append(event)
        return len(self.events)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


_T0 = datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC)


class _Clock:
    """Tickable clock for the ``now`` injection seam."""

    def __init__(self, start: datetime) -> None:
        self._t = start

    def __call__(self) -> datetime:
        return self._t

    def advance(self, delta: timedelta) -> None:
        self._t = self._t + delta


def _make_lead(*, lead_id: str = "lead_1", created_at: datetime = _T0) -> Lead:
    return Lead(
        id=lead_id,
        prediction_id="pred_abc",
        name="Jane Doe",
        email="jane@example.com",
        phone="+1-555-0100",
        role="owner",
        sponsor_id="acme-energy",
        scenario_id=None,
        consent_given_at=_T0,
        fine_snapshot_usd=12345.0,
        created_at=created_at,
        updated_at=created_at,
    )


def _make_request(**overrides: Any) -> LeadCaptureRequest:
    base: dict[str, Any] = {
        "prediction_id": "pred_abc",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0100",
        "role": "owner",
        "sponsor_id": "acme-energy",
        "scenario_id": None,
        "consent_given_at": _T0,
        "fine_snapshot_usd": 12345.0,
        "property_type": "multifamily-housing",
        "gross_floor_area_sqft": 45000.0,
        "year_built": 1925,
        "borough": "brooklyn",
        "predicted_eui": 87.3,
        "projected_fine_usd": 12345.0,
        "at_risk": True,
        "report_url": "https://buildingpulse.example.com/r/pred_abc",
        "request_id": "req_123",
        "trace_id": "trace_abc",
        "actor_session_id": "sess_xyz",
    }
    base.update(overrides)
    return LeadCaptureRequest(**base)


def _build_service(
    *,
    lead_outcomes: list[CaptureOutcome],
    notification_outcomes: list[NotificationDispatchOutcome] | None = None,
    clock: _Clock | None = None,
) -> tuple[
    LeadCaptureUseCaseService,
    FakeLeadResourceService,
    FakeNotificationResourceService,
    FakeAuditService,
]:
    lead = FakeLeadResourceService(outcomes=list(lead_outcomes))
    notify = FakeNotificationResourceService(
        outcomes=list(notification_outcomes or [])
    )
    audit = FakeAuditService()
    svc = LeadCaptureUseCaseService(
        lead_service=lead,  # type: ignore[arg-type]
        notification_service=notify,  # type: ignore[arg-type]
        audit_service=audit,  # type: ignore[arg-type]
        now=clock if clock is not None else _Clock(_T0),
    )
    return svc, lead, notify, audit


# ---------------------------------------------------------------------------
# Acceptance: first call → 1 LeadCaptured + 1 PartnerNotificationDispatched.
# ---------------------------------------------------------------------------


async def test_first_capture_records_lead_captured_and_dispatched() -> None:
    lead = _make_lead()
    svc, lead_fake, notify_fake, audit = _build_service(
        lead_outcomes=[CaptureOutcome(lead=lead, fire=True)],
        notification_outcomes=[
            NotificationDispatchOutcome(
                email=Dispatched(channel="email"), webhook=None
            )
        ],
    )

    result = await svc.capture(_make_request())

    assert isinstance(result, LeadCaptureResult)
    assert result.fire is True
    assert result.lead is lead
    assert result.dispatch is not None

    # One notify call, one audit-log per acceptance criterion.
    assert len(notify_fake.notify_calls) == 1
    assert len(audit.events) == 2
    assert isinstance(audit.events[0], LeadCaptured)
    assert isinstance(audit.events[1], PartnerNotificationDispatched)
    assert audit.events[1].channel == "email"
    assert audit.events[0].lead_id == lead.id
    assert audit.events[0].email == "jane@example.com"
    assert audit.events[0].prediction_id == "pred_abc"
    # Audit-event tracing fields are threaded through from the request.
    for ev in audit.events:
        assert ev.request_id == "req_123"
        assert ev.trace_id == "trace_abc"
        assert ev.actor_session_id == "sess_xyz"
        assert ev.occurred_at == _T0


async def test_first_capture_passes_full_payload_to_notification_service() -> None:
    lead = _make_lead()
    svc, _lead, notify_fake, _audit = _build_service(
        lead_outcomes=[CaptureOutcome(lead=lead, fire=True)],
        notification_outcomes=[
            NotificationDispatchOutcome(
                email=Dispatched(channel="email"), webhook=None
            )
        ],
    )

    await svc.capture(_make_request(scenario_id="heat-pump"))

    [payload] = notify_fake.notify_calls
    assert payload.lead_id == lead.id
    assert payload.prediction_id == "pred_abc"
    assert payload.sponsor_id == "acme-energy"
    assert payload.scenario_id == "heat-pump"
    assert payload.property_type == "multifamily-housing"
    assert payload.gross_floor_area_sqft == 45000.0
    assert payload.year_built == 1925
    assert payload.borough == "brooklyn"
    assert payload.predicted_eui == 87.3
    assert payload.projected_fine_usd == 12345.0
    assert payload.at_risk is True
    assert payload.report_url == "https://buildingpulse.example.com/r/pred_abc"


async def test_lead_resource_called_with_lead_fields_only() -> None:
    """The use-case must not leak prediction-context fields into the lead repo."""

    lead = _make_lead()
    svc, lead_fake, _notify, _audit = _build_service(
        lead_outcomes=[CaptureOutcome(lead=lead, fire=True)],
        notification_outcomes=[
            NotificationDispatchOutcome(
                email=Dispatched(channel="email"), webhook=None
            )
        ],
    )

    await svc.capture(_make_request())

    [call] = lead_fake.capture_calls
    assert set(call.keys()) == {
        "prediction_id",
        "name",
        "email",
        "phone",
        "role",
        "sponsor_id",
        "scenario_id",
        "consent_given_at",
        "fine_snapshot_usd",
    }


# ---------------------------------------------------------------------------
# Acceptance: repeat within window → 1 more LeadCaptured, 0 new dispatch audits.
# ---------------------------------------------------------------------------


async def test_within_window_resubmission_reaudits_but_does_not_renotify() -> None:
    lead = _make_lead()
    svc, _lead, notify_fake, audit = _build_service(
        lead_outcomes=[CaptureOutcome(lead=lead, fire=False)],
    )

    result = await svc.capture(_make_request())

    assert result.fire is False
    assert result.dispatch is None
    # Notification is the seam that must NOT be touched.
    assert notify_fake.notify_calls == []
    # Audit log is the source of truth for attempts — LeadCaptured fires.
    assert len(audit.events) == 1
    assert isinstance(audit.events[0], LeadCaptured)
    assert audit.events[0].lead_id == lead.id


async def test_two_back_to_back_calls_yield_two_lead_captured_one_dispatched() -> None:
    """Drives the full acceptance scenario: first fires, second is suppressed."""

    lead = _make_lead()
    svc, _lead, notify_fake, audit = _build_service(
        lead_outcomes=[
            CaptureOutcome(lead=lead, fire=True),
            CaptureOutcome(lead=lead, fire=False),
        ],
        notification_outcomes=[
            NotificationDispatchOutcome(
                email=Dispatched(channel="email"), webhook=None
            )
        ],
    )

    await svc.capture(_make_request())
    await svc.capture(_make_request(name="Jane R. Doe"))

    assert len(notify_fake.notify_calls) == 1, "second call must not re-fire dispatch"
    lead_captured = [e for e in audit.events if isinstance(e, LeadCaptured)]
    dispatched = [
        e for e in audit.events if isinstance(e, PartnerNotificationDispatched)
    ]
    failed = [e for e in audit.events if isinstance(e, PartnerNotificationFailed)]
    assert len(lead_captured) == 2
    assert len(dispatched) == 1
    assert len(failed) == 0


# ---------------------------------------------------------------------------
# Acceptance: failed dispatch → 1 LeadCaptured + 1 PartnerNotificationFailed.
# ---------------------------------------------------------------------------


async def test_failed_dispatch_records_partner_notification_failed() -> None:
    lead = _make_lead()
    svc, _lead, _notify, audit = _build_service(
        lead_outcomes=[CaptureOutcome(lead=lead, fire=True)],
        notification_outcomes=[
            NotificationDispatchOutcome(
                email=Failed(channel="email", reason="smtp_timeout"),
                webhook=None,
            )
        ],
    )

    await svc.capture(_make_request())

    assert len(audit.events) == 2
    assert isinstance(audit.events[0], LeadCaptured)
    assert isinstance(audit.events[1], PartnerNotificationFailed)
    assert audit.events[1].channel == "email"
    assert audit.events[1].reason == "smtp_timeout"


# ---------------------------------------------------------------------------
# Webhook channel coverage.
# ---------------------------------------------------------------------------


async def test_dispatch_with_webhook_emits_one_audit_per_channel() -> None:
    """When the sponsor wires a webhook the use-case audits both channels."""

    lead = _make_lead()
    svc, _lead, _notify, audit = _build_service(
        lead_outcomes=[CaptureOutcome(lead=lead, fire=True)],
        notification_outcomes=[
            NotificationDispatchOutcome(
                email=Dispatched(channel="email"),
                webhook=Failed(channel="webhook", reason="connection_refused"),
            )
        ],
    )

    await svc.capture(_make_request())

    dispatched = [
        e for e in audit.events if isinstance(e, PartnerNotificationDispatched)
    ]
    failed = [e for e in audit.events if isinstance(e, PartnerNotificationFailed)]
    assert [e.channel for e in dispatched] == ["email"]
    assert [e.channel for e in failed] == ["webhook"]
    assert failed[0].reason == "connection_refused"


# ---------------------------------------------------------------------------
# Defensive: if a future DispatchResult variant is added the loop is a no-op
# rather than crashing the capture flow.
# ---------------------------------------------------------------------------


async def test_unknown_dispatch_result_variant_is_ignored() -> None:
    @dataclass(frozen=True)
    class _Unknown:
        channel: str = "x"

    lead = _make_lead()
    svc, _lead, _notify, audit = _build_service(
        lead_outcomes=[CaptureOutcome(lead=lead, fire=True)],
        notification_outcomes=[
            NotificationDispatchOutcome(
                email=_Unknown(),  # type: ignore[arg-type]
                webhook=None,
            )
        ],
    )

    await svc.capture(_make_request())

    # LeadCaptured still fires; the unknown-variant branch records nothing.
    assert len(audit.events) == 1
    assert isinstance(audit.events[0], LeadCaptured)


# ---------------------------------------------------------------------------
# `now` injection covers the audit `occurred_at` field.
# ---------------------------------------------------------------------------


async def test_audit_occurred_at_uses_injected_now() -> None:
    clock = _Clock(_T0)
    lead = _make_lead()
    svc, _lead, _notify, audit = _build_service(
        lead_outcomes=[CaptureOutcome(lead=lead, fire=True)],
        notification_outcomes=[
            NotificationDispatchOutcome(
                email=Dispatched(channel="email"), webhook=None
            )
        ],
        clock=clock,
    )

    clock.advance(timedelta(seconds=42))
    await svc.capture(_make_request())

    expected = _T0 + timedelta(seconds=42)
    assert all(ev.occurred_at == expected for ev in audit.events)


async def test_dispatch_result_typing_smoke() -> None:
    """Type-check sanity: the channel-result iterator returns DispatchResult."""

    outcome = NotificationDispatchOutcome(
        email=Dispatched(channel="email"),
        webhook=Failed(channel="webhook", reason="x"),
    )
    results: list[DispatchResult] = LeadCaptureUseCaseService._channel_results(outcome)
    assert len(results) == 2


@pytest.mark.parametrize("scenario_id", [None, "envelope"])
async def test_scenario_id_passes_through_to_payload(scenario_id: str | None) -> None:
    lead = _make_lead()
    svc, _lead, notify_fake, _audit = _build_service(
        lead_outcomes=[CaptureOutcome(lead=lead, fire=True)],
        notification_outcomes=[
            NotificationDispatchOutcome(
                email=Dispatched(channel="email"), webhook=None
            )
        ],
    )

    await svc.capture(_make_request(scenario_id=scenario_id))

    assert notify_fake.notify_calls[0].scenario_id == scenario_id
