"""SQLite connection factory.

Sole importer of the `sqlite3` module per the `sql-confined` import-linter
contract. Applies the PRAGMAs the rest of the app expects on every open
connection.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = "./var/buildingpulse.db"


def get_db_path() -> Path:
    return Path(os.environ.get("DB_PATH", DEFAULT_DB_PATH))


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


__all__ = ["DEFAULT_DB_PATH", "connect", "get_db_path"]
