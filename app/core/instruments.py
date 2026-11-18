"""Instrument registry (M0): loads the core watchlist config into the database."""

import sqlite3
from pathlib import Path

import yaml

from app.storage.db import utcnow

ASSET_CLASSES = {
    "equity", "etf", "index", "fx", "bond_future", "commodity", "crypto", "volatility",
}
MAPPING_FIELDS = ("t212_ticker", "finnhub_symbol", "ig_epic", "yf_symbol")
OPTIONAL_FIELDS = ("region", "currency", "exchange", "sector") + MAPPING_FIELDS


class InstrumentConfigError(ValueError):
    pass


def load_core_watchlist(path: Path) -> list[dict]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    items = data.get("instruments", [])
    seen: set[str] = set()
    for item in items:
        for field in ("key", "name", "asset_class"):
            if not item.get(field):
                raise InstrumentConfigError(f"Instrument missing '{field}': {item}")
        if item["asset_class"] not in ASSET_CLASSES:
            raise InstrumentConfigError(
                f"{item['key']}: unknown asset_class '{item['asset_class']}'"
            )
        if item["key"] in seen:
            raise InstrumentConfigError(f"Duplicate instrument key: {item['key']}")
        seen.add(item["key"])
    return items


def seed_core_watchlist(conn: sqlite3.Connection, items: list[dict]) -> int:
    """Upsert instruments and mark them as core watchlist entries. Returns count."""
    now = utcnow()
    for it in items:
        values = {f: it.get(f) for f in OPTIONAL_FIELDS}
        conn.execute(
            f"""INSERT INTO instruments(key, name, asset_class, {", ".join(OPTIONAL_FIELDS)},
                                        created_at, updated_at)
                VALUES (?, ?, ?, {", ".join("?" for _ in OPTIONAL_FIELDS)}, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    name=excluded.name, asset_class=excluded.asset_class,
                    {", ".join(f"{f}=excluded.{f}" for f in OPTIONAL_FIELDS)},
                    updated_at=excluded.updated_at""",
            (it["key"], it["name"], it["asset_class"], *values.values(), now, now),
        )
        conn.execute(
            """INSERT INTO watchlist(instrument_key, entry_type, reason, status, added_at)
               VALUES (?, 'core', 'Core macro set', 'active', ?)
               ON CONFLICT(instrument_key, entry_type) DO NOTHING""",
            (it["key"], now),
        )
    return len(items)
