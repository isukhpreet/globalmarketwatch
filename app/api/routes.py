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


@router.get("/macro/latest")
def macro_latest(request: Request) -> dict:
    """Latest value of every macro series, with previous value, date, source and freshness."""
    settings = request.app.state.settings
    cat_series = request.app.state.catalogue.series
    verified = {s.key: s.verified for s in cat_series}
    order = {s.key: i for i, s in enumerate(cat_series)}   # catalogue order: US → KR, short → long
    with session(settings.db_path) as conn:
        rows = conn.execute(
            """SELECT s.series_key, s.name, s.region, s.unit, s.frequency, s.source,
                      o.obs_date, o.value, o.released_at, o.fetched_at, o.revised,
                      (SELECT p.value FROM macro_obs p WHERE p.series_key = s.series_key
                         AND p.obs_date < o.obs_date ORDER BY p.obs_date DESC LIMIT 1) AS prev
               FROM macro_series s
               LEFT JOIN macro_obs o ON o.series_key = s.series_key AND o.obs_date =
                    (SELECT MAX(obs_date) FROM macro_obs WHERE series_key = s.series_key)
"""
        ).fetchall()
    rows = sorted(rows, key=lambda r: order.get(r["series_key"], len(order)))
    series = []
    for r in rows:
        d = dict(r)
        d["verified"] = verified.get(d["series_key"], True)
        series.append(d)
    return {"count": len(series), "with_data": sum(1 for s in series if s["value"] is not None),
            "series": series}


@router.post("/collectors/macro/{source}/run")
def run_macro_source(source: str, request: Request) -> dict:
    """Run one macro source now (e.g. right after adding its API key)."""
    from fastapi import HTTPException

    from app.collectors.macro.runner import run_source

    cat = request.app.state.catalogue
    if source not in cat.sources:
        raise HTTPException(404, f"Unknown source '{source}'")
    res = run_source(source, cat, request.app.state.settings)
    return {"source": source, "summary": res.summary(), "failed": res.failed}
