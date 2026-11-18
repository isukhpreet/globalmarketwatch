"""JSON API (M5). Phase 1: health and system status."""

from datetime import UTC, datetime

from fastapi import APIRouter, Request

from app import __version__
from app.storage.db import session, table_counts

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/status")
def status(request: Request) -> dict:
    settings = request.app.state.settings
    started: datetime = request.app.state.started_at
    with session(settings.db_path) as conn:
        counts = table_counts(conn)
        schema_version = conn.execute(
            "SELECT MAX(version) AS v FROM schema_version"
        ).fetchone()["v"]
        collectors = [
            dict(r) for r in conn.execute(
                "SELECT * FROM collector_status ORDER BY name"
            ).fetchall()
        ]
        watchlist = [
            dict(r) for r in conn.execute(
                """SELECT i.key, i.name, i.asset_class, i.region, w.entry_type
                   FROM watchlist w JOIN instruments i ON i.key = w.instrument_key
                   WHERE w.status = 'active' ORDER BY i.asset_class, i.region, i.name"""
            ).fetchall()
        ]
    return {
        "version": __version__,
        "env": settings.env,
        "base_currency": settings.base_currency,
        "started_at": started.isoformat(timespec="seconds"),
        "uptime_seconds": int((datetime.now(UTC) - started).total_seconds()),
        "schema_version": schema_version,
        "integrations": settings.enabled_integrations(),
        "collectors": collectors,
        "table_counts": counts,
        "watchlist": watchlist,
    }
