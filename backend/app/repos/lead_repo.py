"""Persistence for the `leads` table.

All SQL is parameterized; no string interpolation crosses into a query.
Datetime columns are stored as ISO-8601 strings and parsed back on read,
so callers above this layer only handle `datetime` objects.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from app.domain.lead import Lead


def _row_to_lead(row: sqlite3.Row | tuple[object, ...]) -> Lead:
    return Lead(
        id=str(row[0]),
        prediction_id=str(row[1]),
        name=str(row[2]),
        email=str(row[3]),
        phone=str(row[4]),
        role=str(row[5]),
        sponsor_id=str(row[6]),
        scenario_id=None if row[7] is None else str(row[7]),
        consent_given_at=datetime.fromisoformat(str(row[8])),
        fine_snapshot_usd=float(row[9]),  # type: ignore[arg-type]
        created_at=datetime.fromisoformat(str(row[10])),
        updated_at=datetime.fromisoformat(str(row[11])),
    )


_SELECT_COLUMNS = (
    "id, prediction_id, name, email, phone, role, "
    "sponsor_id, scenario_id, consent_given_at, fine_snapshot_usd, "
    "created_at, updated_at"
)


class LeadRepo:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, lead: Lead) -> Lead:
        self._conn.execute(
            "INSERT INTO leads ("
            "id, prediction_id, name, email, phone, role, "
            "sponsor_id, scenario_id, consent_given_at, fine_snapshot_usd, "
            "created_at, updated_at"
            ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                lead.id,
                lead.prediction_id,
                lead.name,
                lead.email,
                lead.phone,
                lead.role,
                lead.sponsor_id,
                lead.scenario_id,
                lead.consent_given_at.isoformat(),
                lead.fine_snapshot_usd,
                lead.created_at.isoformat(),
                lead.updated_at.isoformat(),
            ),
        )
        self._conn.commit()
        return lead

    def find_by_prediction_and_email(
        self, *, prediction_id: str, email: str
    ) -> Lead | None:
        row = self._conn.execute(
            f"SELECT {_SELECT_COLUMNS} FROM leads "  # noqa: S608 — column list is a module constant, not user input
            "WHERE prediction_id = ? AND email = ?",
            (prediction_id, email),
        ).fetchone()
        if row is None:
            return None
        return _row_to_lead(row)

    def update_existing(
        self,
        *,
        prediction_id: str,
        email: str,
        name: str,
        phone: str,
        role: str,
        sponsor_id: str,
        scenario_id: str | None,
        consent_given_at: datetime,
        fine_snapshot_usd: float,
        updated_at: datetime,
    ) -> Lead | None:
        cursor = self._conn.execute(
            "UPDATE leads SET "
            "name = ?, phone = ?, role = ?, sponsor_id = ?, scenario_id = ?, "
            "consent_given_at = ?, fine_snapshot_usd = ?, updated_at = ? "
            "WHERE prediction_id = ? AND email = ?",
            (
                name,
                phone,
                role,
                sponsor_id,
                scenario_id,
                consent_given_at.isoformat(),
                fine_snapshot_usd,
                updated_at.isoformat(),
                prediction_id,
                email,
            ),
        )
        self._conn.commit()
        if cursor.rowcount == 0:
            return None
        return self.find_by_prediction_and_email(
            prediction_id=prediction_id, email=email
        )

    def delete_by_prediction_and_email(
        self, *, prediction_id: str, email: str
    ) -> int:
        cursor = self._conn.execute(
            "DELETE FROM leads WHERE prediction_id = ? AND email = ?",
            (prediction_id, email),
        )
        self._conn.commit()
        return cursor.rowcount


__all__ = ["LeadRepo"]
