"""Persistence for the `audit_log` table."""

from __future__ import annotations

import sqlite3


class AuditRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(
        self,
        *,
        event_type: str,
        occurred_at: str,
        request_id: str,
        trace_id: str,
        prediction_id: str | None,
        lead_id: str | None,
        actor_session_id: str,
        payload_json: str,
    ) -> int:
        cursor = self._conn.execute(
            "INSERT INTO audit_log ("
            "event_type, occurred_at, request_id, trace_id, "
            "prediction_id, lead_id, actor_session_id, payload_json"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                event_type,
                occurred_at,
                request_id,
                trace_id,
                prediction_id,
                lead_id,
                actor_session_id,
                payload_json,
            ),
        )
        self._conn.commit()
        row_id = cursor.lastrowid
        if row_id is None:  # pragma: no cover — sqlite3 always sets lastrowid on INSERT
            raise RuntimeError("audit_log insert returned no lastrowid")
        return row_id


__all__ = ["AuditRepo"]
