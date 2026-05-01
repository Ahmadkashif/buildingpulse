"""Integration tests for LeadRepo against in-memory SQLite.

Migrations run end-to-end against the same DB the repo writes to, so the
schema-vs-code coupling is exercised on every test.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from app.domain.lead import Lead
from app.repos.lead_repo import LeadRepo
from app.repos.migrations import run_migrations


@pytest.fixture
def conn() -> Iterator[sqlite3.Connection]:
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    run_migrations(c)
    yield c
    c.close()


@pytest.fixture
def repo(conn: sqlite3.Connection) -> LeadRepo:
    return LeadRepo(conn)


def _make_lead(**overrides: object) -> Lead:
    base = datetime(2026, 5, 1, 10, 30, tzinfo=UTC)
    defaults: dict[str, object] = {
        "id": "lead_1",
        "prediction_id": "pred_1",
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+1-555-0100",
        "role": "owner",
        "sponsor_id": "sponsor_acme",
        "scenario_id": "scenario_heatpump",
        "consent_given_at": base,
        "fine_snapshot_usd": 12345.67,
        "created_at": base,
        "updated_at": base,
    }
    defaults.update(overrides)
    return Lead(**defaults)  # type: ignore[arg-type]


def test_migration_creates_leads_table(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='leads'"
    ).fetchall()
    assert rows == [("leads",)]


def test_insert_round_trip_preserves_all_fields(repo: LeadRepo) -> None:
    lead = _make_lead()
    returned = repo.insert(lead)
    assert returned == lead

    fetched = repo.find_by_prediction_and_email(
        prediction_id=lead.prediction_id, email=lead.email
    )
    assert fetched == lead


def test_insert_with_null_scenario_id(repo: LeadRepo) -> None:
    lead = _make_lead(id="lead_2", scenario_id=None)
    repo.insert(lead)
    fetched = repo.find_by_prediction_and_email(
        prediction_id=lead.prediction_id, email=lead.email
    )
    assert fetched is not None
    assert fetched.scenario_id is None


def test_find_returns_none_when_no_match(repo: LeadRepo) -> None:
    repo.insert(_make_lead())
    assert (
        repo.find_by_prediction_and_email(
            prediction_id="pred_other", email="ada@example.com"
        )
        is None
    )
    assert (
        repo.find_by_prediction_and_email(
            prediction_id="pred_1", email="other@example.com"
        )
        is None
    )


def test_unique_constraint_on_prediction_email(repo: LeadRepo) -> None:
    repo.insert(_make_lead())
    with pytest.raises(sqlite3.IntegrityError):
        repo.insert(_make_lead(id="lead_dup"))


def test_update_existing_overwrites_mutable_fields(repo: LeadRepo) -> None:
    original = _make_lead()
    repo.insert(original)

    new_ts = original.updated_at + timedelta(minutes=5)
    updated = repo.update_existing(
        prediction_id=original.prediction_id,
        email=original.email,
        name="Ada L.",
        phone="+1-555-0199",
        role="manager",
        sponsor_id="sponsor_beta",
        scenario_id=None,
        consent_given_at=new_ts,
        fine_snapshot_usd=99999.99,
        updated_at=new_ts,
    )
    assert updated is not None
    assert updated.id == original.id
    assert updated.prediction_id == original.prediction_id
    assert updated.email == original.email
    assert updated.created_at == original.created_at
    assert updated.name == "Ada L."
    assert updated.phone == "+1-555-0199"
    assert updated.role == "manager"
    assert updated.sponsor_id == "sponsor_beta"
    assert updated.scenario_id is None
    assert updated.consent_given_at == new_ts
    assert updated.fine_snapshot_usd == 99999.99
    assert updated.updated_at == new_ts


def test_update_existing_returns_none_when_no_row_matches(repo: LeadRepo) -> None:
    new_ts = datetime(2026, 5, 1, 11, 0, tzinfo=UTC)
    result = repo.update_existing(
        prediction_id="missing_pred",
        email="nobody@example.com",
        name="x",
        phone="x",
        role="x",
        sponsor_id="x",
        scenario_id=None,
        consent_given_at=new_ts,
        fine_snapshot_usd=0.0,
        updated_at=new_ts,
    )
    assert result is None


def test_distinct_predictions_can_share_email(repo: LeadRepo) -> None:
    repo.insert(_make_lead(id="lead_a", prediction_id="pred_a"))
    repo.insert(_make_lead(id="lead_b", prediction_id="pred_b"))
    a = repo.find_by_prediction_and_email(prediction_id="pred_a", email="ada@example.com")
    b = repo.find_by_prediction_and_email(prediction_id="pred_b", email="ada@example.com")
    assert a is not None
    assert b is not None
    assert a.id == "lead_a"
    assert b.id == "lead_b"
