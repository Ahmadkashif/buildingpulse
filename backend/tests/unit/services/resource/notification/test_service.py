"""Unit tests for NotificationResourceService.

Pins:
- Email is always dispatched.
- Webhook is dispatched only when the sponsor has a webhook URL configured.
- Dispatcher exceptions never propagate; they become Failed results.
- A dispatcher returning Failed is preserved verbatim.
- A dispatcher returning a non-DispatchResult value becomes a Failed.

Self-verification target: 100% branch coverage for the service module.
"""

from __future__ import annotations

import pytest
from app.config import SponsorConfig
from app.domain.notification import (
    Dispatched,
    DispatchResult,
    Failed,
    LeadNotificationPayload,
)
from app.services.resource.notification.service import (
    NotificationDispatchOutcome,
    NotificationResourceService,
)


class _RecordingDispatcher:
    """Spy with a configurable response or side effect."""

    def __init__(
        self,
        *,
        response: DispatchResult | object | None = None,
        raises: Exception | None = None,
    ) -> None:
        self._response = response
        self._raises = raises
        self.calls: list[LeadNotificationPayload] = []

    def send(self, payload: LeadNotificationPayload) -> DispatchResult:
        self.calls.append(payload)
        if self._raises is not None:
            raise self._raises
        return self._response  # type: ignore[return-value]


@pytest.fixture
def sponsor_with_webhook() -> SponsorConfig:
    return SponsorConfig(
        id="acme-energy",
        name="Acme Energy",
        logo_url="https://cdn.example.com/acme-logo.svg",
        cta_label="Talk to a contractor",
        cta_url="https://acme-energy.example.com/contact",
        lead_email="leads@acme-energy.example.com",
        lead_webhook_url="https://hooks.example.com/acme",
    )


@pytest.fixture
def sponsor_email_only() -> SponsorConfig:
    return SponsorConfig(
        id="acme-energy",
        name="Acme Energy",
        logo_url="https://cdn.example.com/acme-logo.svg",
        cta_label="Talk to a contractor",
        cta_url="https://acme-energy.example.com/contact",
        lead_email="leads@acme-energy.example.com",
        lead_webhook_url=None,
    )


@pytest.fixture
def payload() -> LeadNotificationPayload:
    return LeadNotificationPayload(
        lead_id="lead_1",
        prediction_id="pred_1",
        sponsor_id="acme-energy",
        name="Jane Doe",
        email="jane@example.com",
        phone="+1-555-0100",
        role="owner",
        scenario_id="heat-pump",
        property_type="multifamily-housing",
        gross_floor_area_sqft=45000.0,
        year_built=1925,
        borough="brooklyn",
        predicted_eui=87.3,
        projected_fine_usd=12345.0,
        at_risk=True,
        report_url="https://buildingpulse.example.com/report/pred_1",
    )


def test_notify_dispatches_email_and_webhook_when_both_configured(
    sponsor_with_webhook: SponsorConfig, payload: LeadNotificationPayload
) -> None:
    email = _RecordingDispatcher(response=Dispatched(channel="email"))
    webhook = _RecordingDispatcher(response=Dispatched(channel="webhook"))
    service = NotificationResourceService(sponsor_with_webhook, email, webhook)  # type: ignore[arg-type]

    outcome = service.notify(payload)

    assert email.calls == [payload]
    assert webhook.calls == [payload]
    assert outcome == NotificationDispatchOutcome(
        email=Dispatched(channel="email"),
        webhook=Dispatched(channel="webhook"),
    )


def test_notify_skips_webhook_when_sponsor_has_no_webhook_url(
    sponsor_email_only: SponsorConfig, payload: LeadNotificationPayload
) -> None:
    email = _RecordingDispatcher(response=Dispatched(channel="email"))
    webhook = _RecordingDispatcher(response=Dispatched(channel="webhook"))
    service = NotificationResourceService(sponsor_email_only, email, webhook)  # type: ignore[arg-type]

    outcome = service.notify(payload)

    assert email.calls == [payload]
    assert webhook.calls == []
    assert outcome.email == Dispatched(channel="email")
    assert outcome.webhook is None


def test_notify_skips_webhook_when_no_dispatcher_wired(
    sponsor_with_webhook: SponsorConfig, payload: LeadNotificationPayload
) -> None:
    email = _RecordingDispatcher(response=Dispatched(channel="email"))
    service = NotificationResourceService(sponsor_with_webhook, email, None)  # type: ignore[arg-type]

    outcome = service.notify(payload)

    assert outcome.email == Dispatched(channel="email")
    assert outcome.webhook is None


def test_notify_returns_failed_when_email_dispatcher_raises(
    sponsor_with_webhook: SponsorConfig, payload: LeadNotificationPayload
) -> None:
    email = _RecordingDispatcher(raises=RuntimeError("boom"))
    webhook = _RecordingDispatcher(response=Dispatched(channel="webhook"))
    service = NotificationResourceService(sponsor_with_webhook, email, webhook)  # type: ignore[arg-type]

    outcome = service.notify(payload)

    assert isinstance(outcome.email, Failed)
    assert outcome.email.channel == "email"
    assert "boom" in outcome.email.reason
    # webhook still ran — one channel failing must not block the other
    assert outcome.webhook == Dispatched(channel="webhook")


def test_notify_returns_failed_when_webhook_dispatcher_raises(
    sponsor_with_webhook: SponsorConfig, payload: LeadNotificationPayload
) -> None:
    email = _RecordingDispatcher(response=Dispatched(channel="email"))
    webhook = _RecordingDispatcher(raises=ValueError("bad url"))
    service = NotificationResourceService(sponsor_with_webhook, email, webhook)  # type: ignore[arg-type]

    outcome = service.notify(payload)

    assert outcome.email == Dispatched(channel="email")
    assert isinstance(outcome.webhook, Failed)
    assert outcome.webhook.channel == "webhook"
    assert "bad url" in outcome.webhook.reason


def test_notify_preserves_failed_result_returned_by_dispatcher(
    sponsor_with_webhook: SponsorConfig, payload: LeadNotificationPayload
) -> None:
    email = _RecordingDispatcher(
        response=Failed(channel="email", reason="smtp 5xx")
    )
    webhook = _RecordingDispatcher(response=Dispatched(channel="webhook"))
    service = NotificationResourceService(sponsor_with_webhook, email, webhook)  # type: ignore[arg-type]

    outcome = service.notify(payload)

    assert outcome.email == Failed(channel="email", reason="smtp 5xx")
    assert outcome.webhook == Dispatched(channel="webhook")


def test_notify_converts_unexpected_return_value_to_failed(
    sponsor_email_only: SponsorConfig, payload: LeadNotificationPayload
) -> None:
    email = _RecordingDispatcher(response="not-a-result")  # type: ignore[arg-type]
    service = NotificationResourceService(sponsor_email_only, email, None)  # type: ignore[arg-type]

    outcome = service.notify(payload)

    assert isinstance(outcome.email, Failed)
    assert outcome.email.channel == "email"
    assert "non-DispatchResult" in outcome.email.reason
    assert outcome.webhook is None


def test_notify_never_raises_even_when_both_dispatchers_explode(
    sponsor_with_webhook: SponsorConfig, payload: LeadNotificationPayload
) -> None:
    email = _RecordingDispatcher(raises=RuntimeError("smtp down"))
    webhook = _RecordingDispatcher(raises=RuntimeError("dns failure"))
    service = NotificationResourceService(sponsor_with_webhook, email, webhook)  # type: ignore[arg-type]

    outcome = service.notify(payload)  # must not raise

    assert isinstance(outcome.email, Failed)
    assert isinstance(outcome.webhook, Failed)
