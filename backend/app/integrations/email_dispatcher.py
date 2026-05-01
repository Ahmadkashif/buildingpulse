"""Stub :class:`EmailDispatcher` for partner lead notifications.

v1 ships a stub that logs the rendered email body and returns a typed
:class:`Dispatched` result. A real transactional provider (SES/Postmark)
slots in behind this same ``send`` seam without touching any caller — the
calling :class:`~app.services.resource.notification.service.NotificationResourceService`
substitutes a recording fake at this boundary in tests.
"""

from __future__ import annotations

import structlog

from app.domain.notification import (
    Dispatched,
    DispatchResult,
    Failed,
    LeadNotificationPayload,
)

__all__ = ["CHANNEL", "EmailDispatcher", "render_email_body"]

CHANNEL = "email"

_log = structlog.get_logger(__name__)


def render_email_body(payload: LeadNotificationPayload) -> str:
    """Render the plain-text email body sent to the sponsor's lead inbox.

    The body is a flat key/value block — a sales rep should be able to
    read it without a templating engine. Field order matches the PRD's
    documented partner contract so the format does not drift if we add
    fields later.
    """
    scenario = payload.scenario_id if payload.scenario_id is not None else "(none)"
    risk = "AT RISK" if payload.at_risk else "compliant"
    return (
        "New BuildingPulse lead\n"
        "\n"
        f"Lead ID: {payload.lead_id}\n"
        f"Prediction ID: {payload.prediction_id}\n"
        f"Sponsor ID: {payload.sponsor_id}\n"
        "\n"
        "Contact\n"
        f"  Name:  {payload.name}\n"
        f"  Email: {payload.email}\n"
        f"  Phone: {payload.phone}\n"
        f"  Role:  {payload.role}\n"
        "\n"
        "Building\n"
        f"  Property type:    {payload.property_type}\n"
        f"  Gross floor area: {payload.gross_floor_area_sqft:.0f} sqft\n"
        f"  Year built:       {payload.year_built}\n"
        f"  Borough:          {payload.borough}\n"
        "\n"
        "Diagnostic\n"
        f"  Predicted EUI:   {payload.predicted_eui:.1f} kBTU/sqft\n"
        f"  Projected fine:  ${payload.projected_fine_usd:,.0f}\n"
        f"  Verdict:         {risk}\n"
        f"  Scenario chosen: {scenario}\n"
        "\n"
        f"Report URL: {payload.report_url}\n"
    )


class EmailDispatcher:
    """Stub email transport. Logs the rendered body; never raises."""

    def __init__(self, to_address: str) -> None:
        self._to_address = to_address

    def send(self, payload: LeadNotificationPayload) -> DispatchResult:
        try:
            body = render_email_body(payload)
        except Exception as exc:
            _log.error(
                "lead.email.render_failed",
                lead_id=payload.lead_id,
                error=str(exc),
            )
            return Failed(channel=CHANNEL, reason=f"render failed: {exc}")

        _log.info(
            "lead.email.dispatched",
            channel=CHANNEL,
            to=self._to_address,
            lead_id=payload.lead_id,
            prediction_id=payload.prediction_id,
            body=body,
        )
        return Dispatched(channel=CHANNEL)
