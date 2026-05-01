"""LeadCaptureUseCaseService — composes lead + notification + audit.

Workflow (prd.md → user stories 20, 21, 25, 28; issue #70):

1. Persist the lead via :class:`LeadResourceService`. The resource
   service decides whether to insert a fresh row or update an existing
   one within the 1-hour idempotency window and signals which case via
   :class:`~app.services.resource.lead.CaptureOutcome.fire`.
2. **Only when ``fire`` is True** dispatch the partner notification via
   :class:`NotificationResourceService`. Within the idempotency window
   the partner already heard about this lead; do not re-fire.
3. **Always** record a ``LeadCaptured`` audit event — the audit log is
   the source of truth for capture *attempts*, separate from partner
   notification, so a re-submission still leaves a row.
4. **Iff** notification dispatch ran, translate every channel result
   into the matching audit event:
   :class:`PartnerNotificationDispatched` on
   :class:`~app.domain.notification.Dispatched`,
   :class:`PartnerNotificationFailed` on
   :class:`~app.domain.notification.Failed`.

The service holds no repos and no integrations directly — the
``usecases-compose-resources-only`` import-linter contract enforces
that. The notification payload is assembled here from the lead and the
caller-supplied prediction context (building specs, predicted EUI,
projected fine, report URL).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

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
from app.services.resource.audit.service import AuditService
from app.services.resource.lead.service import LeadResourceService
from app.services.resource.notification.service import (
    NotificationDispatchOutcome,
    NotificationResourceService,
)

__all__ = [
    "LeadCaptureRequest",
    "LeadCaptureResult",
    "LeadCaptureUseCaseService",
]


@dataclass(frozen=True, slots=True)
class LeadCaptureRequest:
    """Bundles every field the use-case needs in one immutable record.

    Three groups:

    * Contact + consent fields written to the lead row.
    * Prediction-derived context — building specs, predicted EUI,
      projected fine, the at-risk verdict, and the report URL — used to
      build the notification payload sent to the partner.
    * Tracing fields (``request_id``, ``trace_id``, ``actor_session_id``)
      threaded through onto every audit event so log readers can stitch
      a single capture attempt back together.
    """

    prediction_id: str
    name: str
    email: str
    phone: str
    role: str
    sponsor_id: str
    scenario_id: str | None
    consent_given_at: datetime
    fine_snapshot_usd: float
    property_type: str
    gross_floor_area_sqft: float
    year_built: int
    borough: str
    predicted_eui: float
    projected_fine_usd: float
    at_risk: bool
    report_url: str
    request_id: str
    trace_id: str
    actor_session_id: str


@dataclass(frozen=True, slots=True)
class LeadCaptureResult:
    """What the use-case returns for the controller to shape into a response.

    ``dispatch`` is ``None`` precisely when notification was suppressed
    by the idempotency window — i.e. when ``fire`` was ``False`` on the
    underlying lead capture.
    """

    lead: Lead
    fire: bool
    dispatch: NotificationDispatchOutcome | None


class LeadCaptureUseCaseService:
    """Composes the three resource services that make a lead capture happen."""

    def __init__(
        self,
        *,
        lead_service: LeadResourceService,
        notification_service: NotificationResourceService,
        audit_service: AuditService,
        now: Callable[[], datetime],
    ) -> None:
        self._lead = lead_service
        self._notification = notification_service
        self._audit = audit_service
        self._now = now

    async def capture(self, request: LeadCaptureRequest) -> LeadCaptureResult:
        outcome = self._lead.capture(
            prediction_id=request.prediction_id,
            name=request.name,
            email=request.email,
            phone=request.phone,
            role=request.role,
            sponsor_id=request.sponsor_id,
            scenario_id=request.scenario_id,
            consent_given_at=request.consent_given_at,
            fine_snapshot_usd=request.fine_snapshot_usd,
        )

        dispatch: NotificationDispatchOutcome | None = None
        if outcome.fire:
            payload = LeadNotificationPayload(
                lead_id=outcome.lead.id,
                prediction_id=request.prediction_id,
                sponsor_id=request.sponsor_id,
                name=request.name,
                email=request.email,
                phone=request.phone,
                role=request.role,
                scenario_id=request.scenario_id,
                property_type=request.property_type,
                gross_floor_area_sqft=request.gross_floor_area_sqft,
                year_built=request.year_built,
                borough=request.borough,
                predicted_eui=request.predicted_eui,
                projected_fine_usd=request.projected_fine_usd,
                at_risk=request.at_risk,
                report_url=request.report_url,
            )
            dispatch = self._notification.notify(payload)

        occurred_at = self._now()

        await self._audit.record(
            LeadCaptured(
                occurred_at=occurred_at,
                request_id=request.request_id,
                trace_id=request.trace_id,
                actor_session_id=request.actor_session_id,
                prediction_id=request.prediction_id,
                lead_id=outcome.lead.id,
                email=request.email,
                consent_given_at=request.consent_given_at,
            )
        )

        if dispatch is not None:
            for result in self._channel_results(dispatch):
                await self._record_dispatch_event(
                    result,
                    occurred_at=occurred_at,
                    request=request,
                    lead_id=outcome.lead.id,
                )

        return LeadCaptureResult(
            lead=outcome.lead, fire=outcome.fire, dispatch=dispatch
        )

    @staticmethod
    def _channel_results(
        dispatch: NotificationDispatchOutcome,
    ) -> list[DispatchResult]:
        results: list[DispatchResult] = [dispatch.email]
        if dispatch.webhook is not None:
            results.append(dispatch.webhook)
        return results

    async def _record_dispatch_event(
        self,
        result: DispatchResult,
        *,
        occurred_at: datetime,
        request: LeadCaptureRequest,
        lead_id: str,
    ) -> None:
        if isinstance(result, Dispatched):
            await self._audit.record(
                PartnerNotificationDispatched(
                    occurred_at=occurred_at,
                    request_id=request.request_id,
                    trace_id=request.trace_id,
                    actor_session_id=request.actor_session_id,
                    prediction_id=request.prediction_id,
                    lead_id=lead_id,
                    channel=result.channel,
                )
            )
            return
        if isinstance(result, Failed):
            await self._audit.record(
                PartnerNotificationFailed(
                    occurred_at=occurred_at,
                    request_id=request.request_id,
                    trace_id=request.trace_id,
                    actor_session_id=request.actor_session_id,
                    prediction_id=request.prediction_id,
                    lead_id=lead_id,
                    channel=result.channel,
                    reason=result.reason,
                )
            )
