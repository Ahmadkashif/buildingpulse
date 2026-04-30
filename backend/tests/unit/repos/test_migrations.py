"""Migration runner unit tests.

Covers: schema_migrations bootstrap, idempotency, lexicographic ordering,
empty migrations directory, transactional rollback on failure.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.repos.connection import connect
from app.repos.migrations import run_migrations


@pytest.fixture()
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    yield c
    c.close()


def _write(dir_path: Path, name: str, sql: str) -> None:
    (dir_path / name).write_text(sql)


def test_creates_schema_migrations_table(conn: sqlite3.Connection, tmp_path: Path) -> None:
    run_migrations(conn, tmp_path)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
    ).fetchall()
    assert rows == [("schema_migrations",)]


def test_empty_migrations_dir_is_valid(conn: sqlite3.Connection, tmp_path: Path) -> None:
    assert run_migrations(conn, tmp_path) == []


def test_missing_migrations_dir_is_valid(conn: sqlite3.Connection, tmp_path: Path) -> None:
    assert run_migrations(conn, tmp_path / "does-not-exist") == []


def test_runs_unapplied_migrations(conn: sqlite3.Connection, tmp_path: Path) -> None:
    _write(tmp_path, "0001_a.sql", "CREATE TABLE a (id INTEGER PRIMARY KEY);")
    _write(tmp_path, "0002_b.sql", "CREATE TABLE b (id INTEGER PRIMARY KEY);")

    applied = run_migrations(conn, tmp_path)

    assert applied == ["0001_a.sql", "0002_b.sql"]
    versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
    assert versions == ["0001_a.sql", "0002_b.sql"]
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('a','b')"
        )
    }
    assert tables == {"a", "b"}


def test_skips_already_applied_migrations(conn: sqlite3.Connection, tmp_path: Path) -> None:
    _write(tmp_path, "0001_a.sql", "CREATE TABLE a (id INTEGER PRIMARY KEY);")
    run_migrations(conn, tmp_path)

    _write(tmp_path, "0002_b.sql", "CREATE TABLE b (id INTEGER PRIMARY KEY);")
    applied = run_migrations(conn, tmp_path)

    assert applied == ["0002_b.sql"]


def test_filename_ordering(conn: sqlite3.Connection, tmp_path: Path) -> None:
    _write(tmp_path, "0010_late.sql", "CREATE TABLE late (id INTEGER PRIMARY KEY);")
    _write(tmp_path, "0002_early.sql", "CREATE TABLE early (id INTEGER PRIMARY KEY);")

    applied = run_migrations(conn, tmp_path)

    assert applied == ["0002_early.sql", "0010_late.sql"]


def test_rolls_back_failed_migration(conn: sqlite3.Connection, tmp_path: Path) -> None:
    _write(tmp_path, "0001_ok.sql", "CREATE TABLE ok (id INTEGER PRIMARY KEY);")
    _write(
        tmp_path,
        "0002_bad.sql",
        "CREATE TABLE bad (id INTEGER PRIMARY KEY); THIS IS NOT VALID SQL;",
    )

    with pytest.raises(sqlite3.Error):
        run_migrations(conn, tmp_path)

    versions = [r[0] for r in conn.execute("SELECT version FROM schema_migrations")]
    assert versions == ["0001_ok.sql"]
    bad_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='bad'"
    ).fetchall()
    assert bad_table == []


def test_connect_applies_pragmas_and_creates_parent(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "x.db"
    c = connect(db_path)
    try:
        fk = c.execute("PRAGMA foreign_keys").fetchone()[0]
        journal = c.execute("PRAGMA journal_mode").fetchone()[0]
        assert fk == 1
        assert journal.lower() == "wal"
        assert db_path.parent.exists()
    finally:
        c.close()


def test_connect_uses_db_path_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "env.db"
    monkeypatch.setenv("DB_PATH", str(db_path))
    c = connect()
    try:
        c.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
    finally:
        c.close()
    assert db_path.exists()
