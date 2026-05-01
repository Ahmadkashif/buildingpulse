"""Integration tests for AuditRepo against in-memory SQLite.

The migrations runner is invoked once per test against the same DB the
repo writes to, so the schema-vs-code coupling is exercised end-to-end.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator

import pytest
from app.repos.audit_repo import AuditRepo
from app.repos.migrations import run_migrations


@pytest.fixture
def conn() -> Iterator[sqlite3.Connection]:
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    run_migrations(c)
    yield c
    c.close()


@pytest.fixture
def repo(conn: sqlite3.Connection) -> AuditRepo:
    return AuditRepo(conn)


def test_migration_creates_audit_log_table(conn: sqlite3.Connection) -> None:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'"
    ).fetchall()
    assert rows == [("audit_log",)]


def test_insert_persists_row_and_returns_id(conn: sqlite3.Connection, repo: AuditRepo) -> None:
    payload = json.dumps({"model_version": "v1", "site_eui_kbtu_per_sqft": 87.3})
    rid = repo.insert(
        event_type="prediction_generated",
        occurred_at="2026-05-01T10:30:00+00:00",
        request_id="req_123",
        trace_id="trace_abc",
        prediction_id="pred_1",
        lead_id=None,
        actor_session_id="sess_xyz",
        payload_json=payload,
    )
    assert rid >= 1

    row = conn.execute(
        "SELECT id, event_type, occurred_at, request_id, trace_id, "
        "prediction_id, lead_id, actor_session_id, payload_json "
        "FROM audit_log WHERE id = ?",
        (rid,),
    ).fetchone()
    assert row == (
        rid,
        "prediction_generated",
        "2026-05-01T10:30:00+00:00",
        "req_123",
        "trace_abc",
        "pred_1",
        None,
        "sess_xyz",
        payload,
    )


def test_insert_allows_null_prediction_and_lead_ids(
    conn: sqlite3.Connection, repo: AuditRepo
) -> None:
    repo.insert(
        event_type="sponsor_cta_followed",
        occurred_at="2026-05-01T11:00:00+00:00",
        request_id="r",
        trace_id="t",
        prediction_id=None,
        lead_id=None,
        actor_session_id="sess",
        payload_json="{}",
    )
    row = conn.execute("SELECT prediction_id, lead_id FROM audit_log").fetchone()
    assert row == (None, None)


def test_insert_returns_monotonic_ids(repo: AuditRepo) -> None:
    ids = [
        repo.insert(
            event_type="scenario_selected",
            occurred_at="2026-05-01T10:30:00+00:00",
            request_id=f"req_{i}",
            trace_id="t",
            prediction_id="p",
            lead_id=None,
            actor_session_id="s",
            payload_json="{}",
        )
        for i in range(3)
    ]
    assert ids == sorted(ids)
    assert len(set(ids)) == 3


def test_insert_rejects_missing_required_columns(repo: AuditRepo) -> None:
    with pytest.raises(sqlite3.IntegrityError):
        repo.insert(
            event_type="prediction_generated",
            occurred_at="2026-05-01T10:30:00+00:00",
            request_id="r",
            trace_id="t",
            prediction_id=None,
            lead_id=None,
            actor_session_id=None,  # type: ignore[arg-type]
            payload_json="{}",
        )
