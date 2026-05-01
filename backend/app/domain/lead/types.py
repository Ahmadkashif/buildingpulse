"""Lead domain type.

Mirrors the `leads` table column-for-column. The repo layer constructs
`Lead` instances from `sqlite3.Row` and returns them across the layer
boundary; everything above `app.repos` only ever sees this dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Lead:
    id: str
    prediction_id: str
    name: str
    email: str
    phone: str
    role: str
    sponsor_id: str
    scenario_id: str | None
    consent_given_at: datetime
    fine_snapshot_usd: float
    created_at: datetime
    updated_at: datetime


__all__ = ["Lead"]
