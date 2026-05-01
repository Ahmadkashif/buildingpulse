"""Unit tests for EmailDispatcher.

Pins:
- ``send`` returns Dispatched on the happy path.
- ``send`` returns Failed when rendering raises (does not propagate).
- The rendered body contains the documented lead context fields.
"""

from __future__ import annotations

import dataclasses
from unittest.mock import patch

import pytest
from app.domain.notification import (
    Dispatched,
    Failed,
    LeadNotificationPayload,
)
from app.integrations.email_dispatcher import (
    EmailDispatcher,
    render_email_body,
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


def test_render_email_body_contains_documented_lead_context(
    payload: LeadNotificationPayload,
) -> None:
    body = render_email_body(payload)

    # Identifiers
    assert "lead_1" in body
    assert "pred_1" in body
    assert "acme-energy" in body
    # Contact
    assert "Jane Doe" in body
    assert "jane@example.com" in body
    assert "+1-555-0100" in body
    assert "owner" in body
    # Building specs
    assert "multifamily-housing" in body
    assert "45000 sqft" in body
    assert "1925" in body
    assert "brooklyn" in body
    # Diagnostic
    assert "87.3" in body
    assert "$12,345" in body
    assert "AT RISK" in body
    assert "heat-pump" in body
    # Report URL
    assert "https://buildingpulse.example.com/report/pred_1" in body


def test_render_email_body_marks_compliant_when_not_at_risk(
    payload: LeadNotificationPayload,
) -> None:
    safe = dataclasses.replace(payload, at_risk=False)
    body = render_email_body(safe)
    assert "compliant" in body
    assert "AT RISK" not in body


def test_render_email_body_renders_none_scenario_as_placeholder(
    payload: LeadNotificationPayload,
) -> None:
    no_scenario = dataclasses.replace(payload, scenario_id=None)
    body = render_email_body(no_scenario)
    assert "(none)" in body


def test_send_returns_dispatched_on_happy_path(
    payload: LeadNotificationPayload,
) -> None:
    dispatcher = EmailDispatcher(to_address="leads@acme.example.com")
    result = dispatcher.send(payload)
    assert result == Dispatched(channel="email")


def test_send_returns_failed_when_rendering_raises(
    payload: LeadNotificationPayload,
) -> None:
    dispatcher = EmailDispatcher(to_address="leads@acme.example.com")
    with patch(
        "app.integrations.email_dispatcher.render_email_body",
        side_effect=RuntimeError("template explosion"),
    ):
        result = dispatcher.send(payload)

    assert isinstance(result, Failed)
    assert result.channel == "email"
    assert "template explosion" in result.reason
