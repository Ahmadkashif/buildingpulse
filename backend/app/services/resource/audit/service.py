"""AuditService — the resource service for audit event recording.

Use-case services call `await audit.record(SomeEvent(...))` at audit
points. The service splits the typed event into the eight `audit_log`
columns and a JSON-serialized payload of the event-specific fields.
"""

from __future__ import annotations

import json
from typing import Final

from app.domain.audit.types import AuditEvent
from app.repos.audit_repo import AuditRepo

_COMMON_COLUMNS: Final[frozenset[str]] = frozenset(
    {
        "event_type",
        "occurred_at",
        "request_id",
        "trace_id",
        "actor_session_id",
        "prediction_id",
        "lead_id",
    }
)


class AuditService:
    def __init__(self, repo: AuditRepo) -> None:
        self._repo = repo

    async def record(self, event: AuditEvent) -> int:
        dumped = event.model_dump(mode="json")
        payload = {k: v for k, v in dumped.items() if k not in _COMMON_COLUMNS}
        return self._repo.insert(
            event_type=event.event_type,
            occurred_at=event.occurred_at.isoformat(),
            request_id=event.request_id,
            trace_id=event.trace_id,
            prediction_id=event.prediction_id,
            lead_id=event.lead_id,
            actor_session_id=event.actor_session_id,
            payload_json=json.dumps(payload, sort_keys=True),
        )


__all__ = ["AuditService"]
