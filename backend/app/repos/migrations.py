"""Hand-rolled migration runner.

Reads `app/repos/migrations/*.sql` in lexicographic filename order and
applies any not yet recorded in `schema_migrations`. Each migration runs
inside a single transaction; on failure the transaction is rolled back
and the version is not recorded.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def run_migrations(conn: sqlite3.Connection, migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, "
        "applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"
    )
    applied = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    files = sorted(migrations_dir.glob("*.sql")) if migrations_dir.exists() else []
    newly_applied: list[str] = []
    for path in files:
        version = path.name
        if version in applied:
            continue
        sql = path.read_text()
        escaped = version.replace("'", "''")
        script = (
            "BEGIN;\n"
            f"{sql}\n"
            f"INSERT INTO schema_migrations(version) VALUES ('{escaped}');\n"
            "COMMIT;\n"
        )
        try:
            conn.executescript(script)
        except sqlite3.Error:
            conn.rollback()
            raise
        newly_applied.append(version)
    return newly_applied


__all__ = ["MIGRATIONS_DIR", "run_migrations"]
