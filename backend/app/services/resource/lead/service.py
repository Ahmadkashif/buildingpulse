"""LeadResourceService — owns the lead resource and its idempotency rule.

Composes :class:`~app.repos.lead_repo.LeadRepo` with the policy-defined
1-hour idempotency window (:data:`~app.policy.idempotency.LEAD_IDEMPOTENCY_WINDOW`).
The service is a leaf — it does not import other resource services. The
use-case layer composes this service with notification dispatch.

Idempotency rule (prd.md §"Tradeoffs / known v1 limits")
-------------------------------------------------------
For a given ``(prediction_id, email)``:

* No prior lead row → insert a new lead, signal ``fire`` so the use-case
  layer dispatches the partner notification.
* Prior row whose ``created_at`` is within the window → update the row
  in place, signal ``no-fire`` (the partner already heard about this
  lead within the last hour).
* Prior row whose ``created_at`` is past the window → drop the stale row
  and insert a new lead, signal ``fire``. The drop honours the
  ``leads_prediction_email_idx`` UNIQUE constraint while still producing
  a logically-fresh row.

All time comparisons go through an injectable ``now`` callable so tests
can drive the boundary deterministically.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain.lead import Lead
from app.policy.idempotency import LEAD_IDEMPOTENCY_WINDOW
from app.repos.lead_repo import LeadRepo

__all__ = ["CaptureOutcome", "LeadResourceService"]


@dataclass(frozen=True, slots=True)
class CaptureOutcome:
    """Result of a capture call.

    ``fire`` tells the caller whether to dispatch downstream side effects
    (partner notification, ``LeadCaptured`` audit event). It is ``False``
    only for the within-window update case.
    """

    lead: Lead
    fire: bool


class LeadResourceService:
    """Owns lead persistence and the idempotency-window decision."""

    def __init__(
        self,
        repo: LeadRepo,
        *,
        now: Callable[[], datetime],
        new_id: Callable[[], str] | None = None,
    ) -> None:
        self._repo = repo
        self._now = now
        self._new_id = new_id if new_id is not None else (lambda: str(uuid.uuid4()))

    def find_existing(
        self,
        *,
        prediction_id: str,
        email: str,
        within: timedelta = LEAD_IDEMPOTENCY_WINDOW,
    ) -> Lead | None:
        """Return the prior lead iff one exists *and* is still within ``within``.

        Past-window rows are treated as absent — the caller should plan to
        insert a fresh lead. ``within`` defaults to the policy constant
        and is parameterized only for testability.
        """
        existing = self._repo.find_by_prediction_and_email(
            prediction_id=prediction_id, email=email
        )
        if existing is None:
            return None
        if self._now() - existing.created_at < within:
            return existing
        return None

    def capture(
        self,
        *,
        prediction_id: str,
        name: str,
        email: str,
        phone: str,
        role: str,
        sponsor_id: str,
        scenario_id: str | None,
        consent_given_at: datetime,
        fine_snapshot_usd: float,
    ) -> CaptureOutcome:
        """Persist the lead, signalling whether downstream side effects fire."""
        now = self._now()
        existing = self._repo.find_by_prediction_and_email(
            prediction_id=prediction_id, email=email
        )

        if existing is not None:
            if now - existing.created_at < LEAD_IDEMPOTENCY_WINDOW:
                updated = self._repo.update_existing(
                    prediction_id=prediction_id,
                    email=email,
                    name=name,
                    phone=phone,
                    role=role,
                    sponsor_id=sponsor_id,
                    scenario_id=scenario_id,
                    consent_given_at=consent_given_at,
                    fine_snapshot_usd=fine_snapshot_usd,
                    updated_at=now,
                )
                if updated is None:
                    raise RuntimeError(
                        "lead vanished between find and update for "
                        f"prediction_id={prediction_id!r}"
                    )
                return CaptureOutcome(lead=updated, fire=False)
            self._repo.delete_by_prediction_and_email(
                prediction_id=prediction_id, email=email
            )

        lead = Lead(
            id=self._new_id(),
            prediction_id=prediction_id,
            name=name,
            email=email,
            phone=phone,
            role=role,
            sponsor_id=sponsor_id,
            scenario_id=scenario_id,
            consent_given_at=consent_given_at,
            fine_snapshot_usd=fine_snapshot_usd,
            created_at=now,
            updated_at=now,
        )
        self._repo.insert(lead)
        return CaptureOutcome(lead=lead, fire=True)
