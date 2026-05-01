"""Lead capture idempotency window.

Source authority
----------------
- prd.md §"Tradeoffs / known v1 limits":
  "Idempotency: 1-hour window per (prediction_id, email). Within window,
  update the row but do not re-fire the partner notification. Outside
  window, treat as a new lead. Window length is a constant in policy/."
- prd.md §"User stories" — story 25 (operator wants every lead persisted)
  and story 27 (idempotent re-submission).

The constant is exported as a ``timedelta`` so callers can compare against
``now() - lead.created_at`` directly without re-deriving units.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

__all__ = ["LEAD_IDEMPOTENCY_WINDOW"]


LEAD_IDEMPOTENCY_WINDOW: Final[timedelta] = timedelta(hours=1)
