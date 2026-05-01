"""Unit tests for :class:`LeadResourceService`.

Pinned behaviours:

* First call for a (prediction_id, email) inserts and signals ``fire``.
* Second call within the 1-hour idempotency window updates the row in
  place and signals ``no-fire``.
* Third call outside the window drops the stale row, inserts a new lead
  with a fresh id, and signals ``fire``.
* All time comparisons go through the injected ``now`` callable; the
  service never calls :func:`datetime.now` itself.
* ``find_existing`` honours the same window and returns ``None`` for
  past-window rows, so callers cannot accidentally short-circuit a
  legitimately-new lead.

Self-verification: 100% branch coverage; ``mutmut`` mutation score on
``app/services/resource/lead`` ≥ 90%.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from app.domain.lead import Lead
from app.policy.idempotency import LEAD_IDEMPOTENCY_WINDOW
from app.services.resource.lead.service import (
    CaptureOutcome,
    LeadResourceService,
)


@dataclass
class FakeLeadRepo:
    """In-memory stand-in for :class:`LeadRepo`.

    Mirrors the (prediction_id, email) UNIQUE constraint so tests catch
    the case where the service forgets to drop a stale row before
    inserting a fresh one.
    """

    rows: dict[tuple[str, str], Lead] = field(default_factory=dict)
    insert_calls: list[Lead] = field(default_factory=list)
    update_calls: list[dict[str, Any]] = field(default_factory=list)
    delete_calls: list[tuple[str, str]] = field(default_factory=list)

    def insert(self, lead: Lead) -> Lead:
        key = (lead.prediction_id, lead.email)
        if key in self.rows:
            raise AssertionError(
                f"UNIQUE violation in fake repo for {key!r} — "
                "service must delete the prior row first"
            )
        self.rows[key] = lead
        self.insert_calls.append(lead)
        return lead

    def find_by_prediction_and_email(
        self, *, prediction_id: str, email: str
    ) -> Lead | None:
        return self.rows.get((prediction_id, email))

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
        key = (prediction_id, email)
        old = self.rows.get(key)
        self.update_calls.append(
            {
                "prediction_id": prediction_id,
                "email": email,
                "name": name,
                "phone": phone,
                "role": role,
                "sponsor_id": sponsor_id,
                "scenario_id": scenario_id,
                "consent_given_at": consent_given_at,
                "fine_snapshot_usd": fine_snapshot_usd,
                "updated_at": updated_at,
            }
        )
        if old is None:
            return None
        new = replace(
            old,
            name=name,
            phone=phone,
            role=role,
            sponsor_id=sponsor_id,
            scenario_id=scenario_id,
            consent_given_at=consent_given_at,
            fine_snapshot_usd=fine_snapshot_usd,
            updated_at=updated_at,
        )
        self.rows[key] = new
        return new

    def delete_by_prediction_and_email(
        self, *, prediction_id: str, email: str
    ) -> int:
        key = (prediction_id, email)
        self.delete_calls.append(key)
        return 1 if self.rows.pop(key, None) is not None else 0


class _Clock:
    """Tick-by-tick clock for the ``now`` injection seam."""

    def __init__(self, start: datetime) -> None:
        self._t = start

    def __call__(self) -> datetime:
        return self._t

    def advance(self, delta: timedelta) -> None:
        self._t = self._t + delta


_T0 = datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC)


def _ids(*values: str):
    """Return a callable yielding the given ids in order."""

    pool = iter(values)

    def _next() -> str:
        return next(pool)

    return _next


def _capture_kwargs(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "prediction_id": "pred_abc",
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0100",
        "role": "owner",
        "sponsor_id": "acme-energy",
        "scenario_id": None,
        "consent_given_at": _T0,
        "fine_snapshot_usd": 12345.0,
    }
    base.update(overrides)
    return base


def test_first_capture_inserts_and_signals_fire() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))

    outcome = svc.capture(**_capture_kwargs())

    assert isinstance(outcome, CaptureOutcome)
    assert outcome.fire is True
    assert outcome.lead.id == "lead_1"
    assert outcome.lead.created_at == _T0
    assert outcome.lead.updated_at == _T0
    assert len(repo.insert_calls) == 1
    assert repo.update_calls == []
    assert repo.delete_calls == []
    assert repo.rows[("pred_abc", "jane@example.com")] is outcome.lead


def test_second_capture_within_window_updates_and_signals_no_fire() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1", "lead_2"))

    first = svc.capture(**_capture_kwargs())
    clock.advance(timedelta(minutes=30))
    second = svc.capture(
        **_capture_kwargs(name="Jane R. Doe", phone="+1-555-9999")
    )

    assert second.fire is False
    assert second.lead.id == first.lead.id, "row id is preserved on update"
    assert second.lead.name == "Jane R. Doe"
    assert second.lead.phone == "+1-555-9999"
    assert second.lead.created_at == _T0, "created_at is not bumped on update"
    assert second.lead.updated_at == _T0 + timedelta(minutes=30)
    assert len(repo.insert_calls) == 1
    assert len(repo.update_calls) == 1
    assert repo.delete_calls == []


def test_third_capture_past_window_inserts_fresh_row_and_signals_fire() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(
        repo, now=clock, new_id=_ids("lead_1", "lead_2", "lead_3")
    )

    first = svc.capture(**_capture_kwargs())
    clock.advance(timedelta(minutes=30))
    svc.capture(**_capture_kwargs(name="Update 1"))
    clock.advance(LEAD_IDEMPOTENCY_WINDOW + timedelta(minutes=1))
    third = svc.capture(**_capture_kwargs(name="Much Later"))

    assert third.fire is True
    assert third.lead.id == "lead_2", (
        "third call must produce a new row id, not reuse the prior id"
    )
    assert third.lead.id != first.lead.id
    assert third.lead.created_at == clock()
    assert third.lead.name == "Much Later"
    assert len(repo.insert_calls) == 2
    assert len(repo.delete_calls) == 1
    assert repo.delete_calls[0] == ("pred_abc", "jane@example.com")
    assert repo.rows[("pred_abc", "jane@example.com")] is third.lead


def test_capture_at_exactly_one_hour_boundary_is_outside_window() -> None:
    """Exactly equal to the window is *outside* — the comparison is strict ``<``."""
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1", "lead_2"))

    svc.capture(**_capture_kwargs())
    clock.advance(LEAD_IDEMPOTENCY_WINDOW)
    boundary = svc.capture(**_capture_kwargs(name="Boundary"))

    assert boundary.fire is True
    assert boundary.lead.id == "lead_2"
    assert len(repo.insert_calls) == 2
    assert len(repo.delete_calls) == 1


def test_capture_just_under_window_still_updates_in_place() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))

    svc.capture(**_capture_kwargs())
    clock.advance(LEAD_IDEMPOTENCY_WINDOW - timedelta(microseconds=1))
    nearly = svc.capture(**_capture_kwargs(name="Just Under"))

    assert nearly.fire is False
    assert nearly.lead.id == "lead_1"
    assert len(repo.insert_calls) == 1
    assert len(repo.update_calls) == 1


def test_capture_uses_injected_now_for_timestamps() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))

    captured = svc.capture(**_capture_kwargs())

    assert captured.lead.created_at == _T0
    assert captured.lead.updated_at == _T0
    clock.advance(timedelta(seconds=42))
    captured2 = svc.capture(**_capture_kwargs(name="Tick"))
    assert captured2.lead.updated_at == _T0 + timedelta(seconds=42)


def test_default_new_id_generates_unique_ids() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock)

    a = svc.capture(**_capture_kwargs())
    clock.advance(LEAD_IDEMPOTENCY_WINDOW + timedelta(minutes=1))
    b = svc.capture(**_capture_kwargs())

    assert a.lead.id != b.lead.id
    assert len(a.lead.id) > 0


def test_find_existing_returns_none_when_no_row_exists() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock)

    found = svc.find_existing(prediction_id="pred_abc", email="nobody@example.com")

    assert found is None


def test_find_existing_returns_lead_when_within_window() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))
    svc.capture(**_capture_kwargs())
    clock.advance(timedelta(minutes=30))

    found = svc.find_existing(
        prediction_id="pred_abc", email="jane@example.com"
    )

    assert found is not None
    assert found.id == "lead_1"


def test_find_existing_returns_none_when_past_window() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))
    svc.capture(**_capture_kwargs())
    clock.advance(LEAD_IDEMPOTENCY_WINDOW + timedelta(minutes=1))

    found = svc.find_existing(
        prediction_id="pred_abc", email="jane@example.com"
    )

    assert found is None


def test_find_existing_at_boundary_is_outside_window() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))
    svc.capture(**_capture_kwargs())
    clock.advance(LEAD_IDEMPOTENCY_WINDOW)

    found = svc.find_existing(
        prediction_id="pred_abc", email="jane@example.com"
    )

    assert found is None


def test_find_existing_honours_custom_within() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))
    svc.capture(**_capture_kwargs())
    clock.advance(timedelta(minutes=10))

    short = svc.find_existing(
        prediction_id="pred_abc",
        email="jane@example.com",
        within=timedelta(minutes=5),
    )
    long_ = svc.find_existing(
        prediction_id="pred_abc",
        email="jane@example.com",
        within=timedelta(minutes=30),
    )

    assert short is None
    assert long_ is not None


def test_capture_passes_all_fields_through_to_repo_insert() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))
    consent = datetime(2026, 4, 30, 9, 0, tzinfo=UTC)

    outcome = svc.capture(
        **_capture_kwargs(
            scenario_id="heat-pump",
            consent_given_at=consent,
            fine_snapshot_usd=98765.5,
        )
    )

    saved = repo.insert_calls[0]
    assert saved is outcome.lead
    assert saved.prediction_id == "pred_abc"
    assert saved.email == "jane@example.com"
    assert saved.phone == "+1-555-0100"
    assert saved.role == "owner"
    assert saved.sponsor_id == "acme-energy"
    assert saved.scenario_id == "heat-pump"
    assert saved.consent_given_at == consent
    assert saved.fine_snapshot_usd == 98765.5
    assert saved.created_at == _T0
    assert saved.updated_at == _T0


def test_capture_passes_all_fields_through_to_repo_update() -> None:
    repo = FakeLeadRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))
    svc.capture(**_capture_kwargs())
    clock.advance(timedelta(minutes=15))
    new_consent = datetime(2026, 4, 30, 10, 0, tzinfo=UTC)

    svc.capture(
        **_capture_kwargs(
            name="Updated Name",
            phone="+1-555-0200",
            role="manager",
            sponsor_id="other-sponsor",
            scenario_id="envelope",
            consent_given_at=new_consent,
            fine_snapshot_usd=22222.0,
        )
    )

    args = repo.update_calls[0]
    assert args["prediction_id"] == "pred_abc"
    assert args["email"] == "jane@example.com"
    assert args["name"] == "Updated Name"
    assert args["phone"] == "+1-555-0200"
    assert args["role"] == "manager"
    assert args["sponsor_id"] == "other-sponsor"
    assert args["scenario_id"] == "envelope"
    assert args["consent_given_at"] == new_consent
    assert args["fine_snapshot_usd"] == 22222.0
    assert args["updated_at"] == _T0 + timedelta(minutes=15)


def test_capture_raises_if_repo_update_returns_none_after_find() -> None:
    """Defensive: if the repo loses the row between find and update we surface it."""

    class FlakyRepo(FakeLeadRepo):
        def update_existing(self, **kwargs: Any) -> Lead | None:  # type: ignore[override]
            super().update_existing(**kwargs)
            return None

    repo = FlakyRepo()
    clock = _Clock(_T0)
    svc = LeadResourceService(repo, now=clock, new_id=_ids("lead_1"))
    svc.capture(**_capture_kwargs())
    clock.advance(timedelta(minutes=5))

    with pytest.raises(RuntimeError, match=r"^lead vanished between find and update"):
        svc.capture(**_capture_kwargs(name="Update"))
