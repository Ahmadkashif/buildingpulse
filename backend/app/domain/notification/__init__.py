"""Notification domain types."""

from app.domain.notification.types import (
    Dispatched,
    DispatchResult,
    Failed,
    LeadNotificationPayload,
)

__all__ = [
    "DispatchResult",
    "Dispatched",
    "Failed",
    "LeadNotificationPayload",
]
