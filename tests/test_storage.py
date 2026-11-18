from app.storage.db import (
    SCHEMA_VERSION,
    init_db,
    list_tables,
    record_status,
    session,
)

EXPECTED_TABLES = {
    "schema_version", "instruments", "watchlist", "watch_tiers", "prices_tick",
    "prices_bar", "macro_series", "macro_obs", "events", "news", "accounts",
    "transactions", "positions", "alerts_rules", "alerts_log", "briefings",
    "collector_status",
}


def test_init_creates_all_tables(tmp_path):
    db = tmp_path / "a.sqlite"
    assert init_db(db) == SCHEMA_VERSION
    with session(db) as conn:
        assert EXPECTED_TABLES <= set(list_tables(conn))


def test_init_is_idempotent(tmp_path):
    db = tmp_path / "a.sqlite"
    init_db(db)
    init_db(db)
    with session(db) as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM schema_version").fetchone()["n"]
    assert n == 1


def test_wal_mode(tmp_path):
    db = tmp_path / "a.sqlite"
    init_db(db)
    with session(db) as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_record_status_success_then_error(tmp_path):
    db = tmp_path / "a.sqlite"
    init_db(db)
    with session(db) as conn:
        record_status(conn, "fred", ok=True, detail="12 series")
        record_status(conn, "fred", ok=False, error="timeout")
        row = conn.execute("SELECT * FROM collector_status WHERE name='fred'").fetchone()
    assert row["last_success"] and row["last_error"]
    assert row["detail"] == "12 series" and row["last_error_msg"] == "timeout"


def test_transactions_deduplicate_on_source_id(tmp_path):
    """Architecture §9 rule 2: one trade arriving via API and CSV is stored once."""
    db = tmp_path / "a.sqlite"
    init_db(db)
    with session(db) as conn:
        conn.execute("INSERT INTO accounts(name, kind) VALUES ('T212 ISA', 't212_isa')")
        sql = """INSERT OR IGNORE INTO transactions
                 (account_id, tx_type, ts, quantity, source, source_id)
                 VALUES (1, 'buy', '2026-11-01T10:00:00Z', 5, ?, 'ORD123')"""
        conn.execute(sql, ("api",))
        conn.execute(sql, ("csv",))
        n = conn.execute("SELECT COUNT(*) AS n FROM transactions").fetchone()["n"]
    assert n == 1
