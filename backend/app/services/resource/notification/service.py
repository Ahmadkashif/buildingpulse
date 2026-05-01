"""NotificationResourceService — orchestrates partner lead dispatchers.

This service composes :class:`~app.integrations.email_dispatcher.EmailDispatcher`
and :class:`~app.integrations.webhook_dispatcher.WebhookDispatcher` per
the active sponsor's config:

- The sponsor's ``lead_email`` is required, so the email dispatcher is
  always invoked.
- The sponsor's ``lead_webhook_url`` is optional; the webhook dispatcher
  is only invoked when the URL is configured at deploy time.

The service never raises. If a dispatcher raises, the exception is
caught, logged, and converted into a :class:`Failed` result. Callers
inspect the returned :class:`NotificationDispatchOutcome` and decide
whether to record :class:`PartnerNotificationDispatched` or
:class:`PartnerNotificationFailed` audit events upstream — the lead
capture API still returns ``201`` even when partner dispatch fails.
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from app.config import SponsorConfig
from app.domain.notification import (
    Dispatched,
    DispatchResult,
    Failed,
    LeadNotificationPayload,
)
from app.integrations.email_dispatcher import EmailDispatcher
from app.integrations.webhook_dispatcher import WebhookDispatcher

__all__ = [
    "NotificationDispatchOutcome",
    "NotificationResourceService",
]

_log = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class NotificationDispatchOutcome:
    """The aggregated result of a single ``notify`` call.

    ``email`` is always present — the email channel is required. ``webhook``
    is ``None`` when the sponsor has no webhook URL configured, signalling
    "did not attempt" rather than "attempted and failed".
    """

    email: DispatchResult
    webhook: DispatchResult | None


class NotificationResourceService:
    """Owns the per-sponsor lead-notification dispatch flow."""

    def __init__(
        self,
        sponsor: SponsorConfig,
        email_dispatcher: EmailDispatcher,
        webhook_dispatcher: WebhookDispatcher | None,
    ) -> None:
        self._sponsor = sponsor
        self._email = email_dispatcher
        self._webhook = webhook_dispatcher

    def notify(self, payload: LeadNotificationPayload) -> NotificationDispatchOutcome:
        """Dispatch the lead notification to all configured channels.

        Email is always attempted. The webhook is attempted only when the
        sponsor has ``lead_webhook_url`` configured *and* a webhook
        dispatcher was wired in. Either dispatcher raising is caught and
        recorded as :class:`Failed`; the other channel still runs.
        """
        email_result = self._dispatch(self._email.send, payload, channel="email")

        webhook_result: DispatchResult | None = None
        if self._sponsor.lead_webhook_url is not None and self._webhook is not None:
            webhook_result = self._dispatch(
                self._webhook.send, payload, channel="webhook"
            )

        return NotificationDispatchOutcome(email=email_result, webhook=webhook_result)

    @staticmethod
    def _dispatch(
        send: object, payload: LeadNotificationPayload, *, channel: str
    ) -> DispatchResult:
        try:
            result = send(payload)  # type: ignore[operator]
        except Exception as exc:
            _log.error(
                "lead.notification.dispatch_raised",
                channel=channel,
                lead_id=payload.lead_id,
                error=str(exc),
            )
            return Failed(channel=channel, reason=f"dispatcher raised: {exc}")

        if isinstance(result, Failed):
            _log.warning(
                "lead.notification.dispatch_failed",
                channel=channel,
                lead_id=payload.lead_id,
                reason=result.reason,
            )
            return result
        if isinstance(result, Dispatched):
            return result

        _log.error(
            "lead.notification.dispatch_returned_invalid",
            channel=channel,
            lead_id=payload.lead_id,
            got=type(result).__name__,
        )
        return Failed(
            channel=channel,
            reason=f"dispatcher returned non-DispatchResult: {type(result).__name__}",
        )
