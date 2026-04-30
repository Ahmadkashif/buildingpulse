"""Pydantic discriminated union of every audit event the system emits.

The seven members map 1:1 to the audit points listed in `prd.md` →
"Audit logging". Common columns (`occurred_at`, `request_id`, `trace_id`,
`actor_session_id`, `prediction_id?`, `lead_id?`) appear as top-level
fields on every member; event-specific fields live alongside them and the
service serializes them into `payload_json` at write time.

The `event_type` field is the union discriminator. Pydantic enforces
exhaustiveness on parse and `match` statements over `event_type` are
checked by mypy/pyright.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class _AuditBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    occurred_at: datetime
    request_id: str
    trace_id: str
    actor_session_id: str
    prediction_id: str | None = None
    lead_id: str | None = None


class PredictionGenerated(_AuditBase):
    event_type: Literal["prediction_generated"] = "prediction_generated"
    model_version: str
    site_eui_kbtu_per_sqft: float


class LeadCaptured(_AuditBase):
    event_type: Literal["lead_captured"] = "lead_captured"
    email: str
    consent_given_at: datetime


class PartnerNotificationDispatched(_AuditBase):
    event_type: Literal["partner_notification_dispatched"] = "partner_notification_dispatched"
    channel: str


class PartnerNotificationFailed(_AuditBase):
    event_type: Literal["partner_notification_failed"] = "partner_notification_failed"
    channel: str
    reason: str


class ScenarioSelected(_AuditBase):
    event_type: Literal["scenario_selected"] = "scenario_selected"
    scenario_id: str


class PdfGenerated(_AuditBase):
    event_type: Literal["pdf_generated"] = "pdf_generated"
    bytes_size: int


class SponsorCtaFollowed(_AuditBase):
    event_type: Literal["sponsor_cta_followed"] = "sponsor_cta_followed"
    scenario_id: str | None = None


AuditEvent = Annotated[
    PredictionGenerated
    | LeadCaptured
    | PartnerNotificationDispatched
    | PartnerNotificationFailed
    | ScenarioSelected
    | PdfGenerated
    | SponsorCtaFollowed,
    Field(discriminator="event_type"),
]


__all__ = [
    "AuditEvent",
    "LeadCaptured",
    "PartnerNotificationDispatched",
    "PartnerNotificationFailed",
    "PdfGenerated",
    "PredictionGenerated",
    "ScenarioSelected",
    "SponsorCtaFollowed",
]
