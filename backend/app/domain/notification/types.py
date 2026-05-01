"""Domain types for the partner-notification role.

The notification payload mirrors the lead context the PRD pins as the
contract with the sponsor partner: contact fields, the originating
prediction id, the building specs, the predicted EUI, the projected
fine, the at-risk verdict, and the report URL. Dispatchers in
``app.integrations`` consume an immutable :class:`LeadNotificationPayload`
and return a discriminated :class:`DispatchResult`.

A `channel` string identifies which transport produced the result so
callers (and audit events upstream) can attribute success or failure
without having to introspect the dispatcher object.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "DispatchResult",
    "Dispatched",
    "Failed",
    "LeadNotificationPayload",
]


@dataclass(frozen=True, slots=True)
class LeadNotificationPayload:
    """The full lead context handed to every dispatcher.

    Field set is the PRD-pinned partner contract. Keep additive; removals
    or renames are a breaking change for downstream sponsor CRMs.
    """

    lead_id: str
    prediction_id: str
    sponsor_id: str
    name: str
    email: str
    phone: str
    role: str
    scenario_id: str | None
    property_type: str
    gross_floor_area_sqft: float
    year_built: int
    borough: str
    predicted_eui: float
    projected_fine_usd: float
    at_risk: bool
    report_url: str


@dataclass(frozen=True, slots=True)
class Dispatched:
    """A successful dispatch on the named ``channel``."""

    channel: str


@dataclass(frozen=True, slots=True)
class Failed:
    """A failed dispatch on the named ``channel``.

    ``reason`` is human-readable text suitable for an audit event or log
    line; it is not parsed downstream.
    """

    channel: str
    reason: str


DispatchResult = Dispatched | Failed
