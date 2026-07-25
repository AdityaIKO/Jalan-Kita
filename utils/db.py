"""SQLite persistence engine (standard-library `sqlite3`, no extra dependency).

Replaces the previous "rewrite the whole JSON file on every change" approach,
which was prone to race conditions when two people acted at once. SQLite gives
atomic, transactional writes and real durability on any host with a stable disk
(local machine, VM, or container with a mounted volume).

The public API mirrors how the app already thinks about data: a collection is a
list of dict records, loaded and saved whole. Each record's full dict is stored
as JSON in a `data` column, with the primary key and insertion order preserved,
so every existing field keeps working with zero schema churn.

Note on Streamlit Community Cloud: its filesystem is ephemeral, so for permanent
cloud storage point `JALANKITA_DB` at a mounted volume or swap this engine for a
managed Postgres. The API here is written so that swap is a single-file change.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = Path(os.getenv("JALANKITA_DB", str(DATA_DIR / "jalankita.db")))

_lock = threading.Lock()
_initialised = False

# collection name -> primary key field on each record
_KEYS = {"reports": "id", "users": "username"}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    global _initialised
    if _initialised:
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock, _connect() as c:
        for table in _KEYS:
            c.execute(
                f"CREATE TABLE IF NOT EXISTS {table} "
                "(key TEXT PRIMARY KEY, seq INTEGER, data TEXT NOT NULL)"
            )
        c.commit()
    _initialised = True


def count(table: str) -> int:
    init_db()
    with _lock, _connect() as c:
        return c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def load_all(table: str) -> list:
    """Return every record in insertion order as a list of dicts."""
    init_db()
    with _lock, _connect() as c:
        rows = c.execute(f"SELECT data FROM {table} ORDER BY seq").fetchall()
    out = []
    for (blob,) in rows:
        try:
            out.append(json.loads(blob))
        except (TypeError, json.JSONDecodeError):
            continue
    return out


def save_all(table: str, items: list) -> None:
    """Replace the whole collection atomically, preserving list order."""
    init_db()
    key_field = _KEYS[table]
    rows = []
    for i, item in enumerate(items):
        key = str(item.get(key_field, i))
        rows.append((key, i, json.dumps(item, ensure_ascii=False)))
    with _lock, _connect() as c:
        c.execute("BEGIN")
        c.execute(f"DELETE FROM {table}")
        c.executemany(f"INSERT INTO {table} (key, seq, data) VALUES (?, ?, ?)", rows)
        c.commit()
