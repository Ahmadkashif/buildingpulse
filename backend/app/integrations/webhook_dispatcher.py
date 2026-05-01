"""Stub :class:`WebhookDispatcher` for partner lead notifications.

v1 ships a stub that logs the JSON-shaped payload and returns a typed
:class:`Dispatched` result. A real HTTP POST (httpx) slots in behind the
same ``send`` seam without touching callers.
"""

from __future__ import annotations

from dataclasses import asdict

import structlog

from app.domain.notification import (
    Dispatched,
    DispatchResult,
    Failed,
    LeadNotificationPayload,
)

__all__ = ["CHANNEL", "WebhookDispatcher", "render_webhook_payload"]

CHANNEL = "webhook"

_log = structlog.get_logger(__name__)


def render_webhook_payload(payload: LeadNotificationPayload) -> dict[str, object]:
    """Project the lead notification into a flat JSON-serialisable dict."""
    return asdict(payload)


class WebhookDispatcher:
    """Stub webhook transport. Logs the body; never raises."""

    def __init__(self, target_url: str) -> None:
        self._target_url = target_url

    def send(self, payload: LeadNotificationPayload) -> DispatchResult:
        try:
            body = render_webhook_payload(payload)
        except Exception as exc:
            _log.error(
                "lead.webhook.render_failed",
                lead_id=payload.lead_id,
                error=str(exc),
            )
            return Failed(channel=CHANNEL, reason=f"render failed: {exc}")

        _log.info(
            "lead.webhook.dispatched",
            channel=CHANNEL,
            url=self._target_url,
            lead_id=payload.lead_id,
            prediction_id=payload.prediction_id,
            body=body,
        )
        return Dispatched(channel=CHANNEL)
