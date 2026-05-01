"""Persistence for the `audit_log` table."""

from __future__ import annotations

import sqlite3


class AuditRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def prediction_exists(self, prediction_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM audit_log "
            "WHERE event_type = 'prediction_generated' AND prediction_id = ? "
            "LIMIT 1",
            (prediction_id,),
        ).fetchone()
        return row is not None

    def scenario_selected_exists_since(
        self,
        *,
        prediction_id: str,
        scenario_id: str,
        since_iso: str,
    ) -> bool:
        """True if a ``scenario_selected`` row for this (prediction, scenario)
        was written at or after ``since_iso``. Used by the select endpoint
        to dedupe rapid double-clicks server-side."""
        row = self._conn.execute(
            "SELECT 1 FROM audit_log "
            "WHERE event_type = 'scenario_selected' "
            "AND prediction_id = ? "
            "AND occurred_at >= ? "
            "AND json_extract(payload_json, '$.scenario_id') = ? "
            "LIMIT 1",
            (prediction_id, since_iso, scenario_id),
        ).fetchone()
        return row is not None

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
