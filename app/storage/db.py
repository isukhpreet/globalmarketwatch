"""SQLite storage helpers (M1).

One database file, WAL mode so the web server can read while collectors write.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

SCHEMA_VERSION = 1
SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


@contextmanager
def session(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Open a connection, commit on success, roll back on error, always close."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path) -> int:
    """Create all tables if missing. Safe to run on every start. Returns schema version."""
    with session(db_path) as conn:
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
        if row["v"] is None:
            conn.execute(
                "INSERT INTO schema_version(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, utcnow()),
            )
            return SCHEMA_VERSION
        return int(row["v"])


def list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    return {
        t: conn.execute(f'SELECT COUNT(*) AS n FROM "{t}"').fetchone()["n"]
        for t in list_tables(conn)
    }


def record_status(
    conn: sqlite3.Connection, name: str, ok: bool | None, detail: str = "", error: str = ""
) -> None:
    """Record a collector's success (ok=True), failure (ok=False) or a neutral note
    such as 'not configured' (ok=None, updates the detail only)."""
    now = utcnow()
    if ok is None:
        conn.execute(
            """INSERT INTO collector_status(name, detail) VALUES (?, ?)
               ON CONFLICT(name) DO UPDATE SET detail=excluded.detail""",
            (name, detail),
        )
    elif ok:
        conn.execute(
            """INSERT INTO collector_status(name, last_success, detail) VALUES (?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET last_success=excluded.last_success,
                                               detail=excluded.detail""",
            (name, now, detail),
        )
    else:
        conn.execute(
            """INSERT INTO collector_status(name, last_error, last_error_msg) VALUES (?, ?, ?)
               ON CONFLICT(name) DO UPDATE SET last_error=excluded.last_error,
                                               last_error_msg=excluded.last_error_msg""",
            (name, now, error[:500]),
        )
