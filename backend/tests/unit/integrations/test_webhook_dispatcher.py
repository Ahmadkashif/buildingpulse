"""Unit tests for WebhookDispatcher."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from app.domain.notification import (
    Dispatched,
    Failed,
    LeadNotificationPayload,
)
from app.integrations.webhook_dispatcher import (
    WebhookDispatcher,
    render_webhook_payload,
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
        scenario_id=None,
        property_type="office",
        gross_floor_area_sqft=120000.0,
        year_built=1972,
        borough="manhattan",
        predicted_eui=110.4,
        projected_fine_usd=98765.0,
        at_risk=True,
        report_url="https://buildingpulse.example.com/report/pred_1",
    )


def test_render_webhook_payload_includes_full_lead_context(
    payload: LeadNotificationPayload,
) -> None:
    body = render_webhook_payload(payload)
    assert body["lead_id"] == "lead_1"
    assert body["prediction_id"] == "pred_1"
    assert body["sponsor_id"] == "acme-energy"
    assert body["email"] == "jane@example.com"
    assert body["property_type"] == "office"
    assert body["gross_floor_area_sqft"] == 120000.0
    assert body["projected_fine_usd"] == 98765.0
    assert body["at_risk"] is True
    assert body["report_url"] == "https://buildingpulse.example.com/report/pred_1"
    assert body["scenario_id"] is None


def test_send_returns_dispatched_on_happy_path(
    payload: LeadNotificationPayload,
) -> None:
    dispatcher = WebhookDispatcher(target_url="https://hooks.example.com/acme")
    result = dispatcher.send(payload)
    assert result == Dispatched(channel="webhook")


def test_send_returns_failed_when_rendering_raises(
    payload: LeadNotificationPayload,
) -> None:
    dispatcher = WebhookDispatcher(target_url="https://hooks.example.com/acme")
    with patch(
        "app.integrations.webhook_dispatcher.render_webhook_payload",
        side_effect=RuntimeError("serializer explosion"),
    ):
        result = dispatcher.send(payload)

    assert isinstance(result, Failed)
    assert result.channel == "webhook"
    assert "serializer explosion" in result.reason
