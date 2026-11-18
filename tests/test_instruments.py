import pytest

from app.core.config import PROJECT_ROOT
from app.core.instruments import (
    InstrumentConfigError,
    load_core_watchlist,
    seed_core_watchlist,
)
from app.storage.db import init_db, session

CORE = PROJECT_ROOT / "config" / "core_watchlist.yaml"


def test_core_watchlist_is_valid():
    items = load_core_watchlist(CORE)
    keys = {i["key"] for i in items}
    assert len(items) >= 10
    # Coverage required by the architecture: US, JP, KR, EU, UK
    regions = {i.get("region") for i in items}
    assert {"US", "JP", "KR", "EU", "UK"} <= regions
    assert {"FX.GBPUSD", "FX.USDJPY", "IDX.SPX"} <= keys


def test_seed_is_idempotent(tmp_path):
    db = tmp_path / "a.sqlite"
    init_db(db)
    items = load_core_watchlist(CORE)
    with session(db) as conn:
        seed_core_watchlist(conn, items)
        seed_core_watchlist(conn, items)
        n_inst = conn.execute("SELECT COUNT(*) AS n FROM instruments").fetchone()["n"]
        n_watch = conn.execute("SELECT COUNT(*) AS n FROM watchlist").fetchone()["n"]
    assert n_inst == len(items) == n_watch


@pytest.mark.parametrize("bad, msg", [
    ("instruments:\n  - {key: A, name: A}\n", "asset_class"),
    ("instruments:\n  - {key: A, name: A, asset_class: shoes}\n", "unknown asset_class"),
    (
        "instruments:\n"
        "  - {key: A, name: A, asset_class: fx}\n"
        "  - {key: A, name: B, asset_class: fx}\n",
        "Duplicate",
    ),
])
def test_invalid_config_rejected(tmp_path, bad, msg):
    p = tmp_path / "w.yaml"
    p.write_text(bad)
    with pytest.raises(InstrumentConfigError, match=msg):
        load_core_watchlist(p)
