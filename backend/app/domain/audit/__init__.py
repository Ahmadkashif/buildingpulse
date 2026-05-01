"""Audit event domain types."""

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
