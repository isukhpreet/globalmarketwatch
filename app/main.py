"""GlobalMarketWatch entry point.

Starts one process containing the web server and the background scheduler.
Run with:  uvicorn app.main:app --port 8000
"""

from contextlib import asynccontextmanager
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes import router
from app.collectors.macro.catalogue import Catalogue, load_catalogue, seed_series
from app.collectors.macro.runner import schedule_macro
from app.core.config import Settings, get_settings
from app.core.instruments import load_core_watchlist, seed_core_watchlist
from app.core.logging import get_logger, setup_logging
from app.storage.db import init_db, record_status, session

log = get_logger("gmw")


def heartbeat(settings: Settings) -> None:
    """Proves the scheduler is alive; shown on the status page."""
    with session(settings.db_path) as conn:
        record_status(conn, "system.heartbeat", ok=True, detail="scheduler alive")


def startup(settings: Settings) -> Catalogue:
    version = init_db(settings.db_path)
    items = load_core_watchlist(settings.config_dir / "core_watchlist.yaml")
    catalogue = load_catalogue(settings.config_dir / "series.yaml")
    with session(settings.db_path) as conn:
        n = seed_core_watchlist(conn, items)
        m = seed_series(conn, catalogue)
        record_status(conn, "system.startup", ok=True, detail=f"v{__version__}")
    log.info("Database ready (schema v%s), %d core instruments, %d macro series", version, n, m)
    return catalogue


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.catalogue = startup(settings)
        heartbeat(settings)
        scheduler = AsyncIOScheduler(timezone="UTC")
        scheduler.add_job(
            heartbeat, "interval", seconds=settings.heartbeat_seconds,
            args=[settings], id="heartbeat",
        )
        if settings.collectors_enabled:
            jobs = schedule_macro(scheduler, app.state.catalogue, settings)
            log.info("Scheduled %d macro collection jobs", len(jobs))
        scheduler.start()
        app.state.scheduler = scheduler
        log.info("GlobalMarketWatch %s started (%s)", __version__, settings.env)
        yield
        scheduler.shutdown(wait=False)
        log.info("GlobalMarketWatch stopped")

    app = FastAPI(title="GlobalMarketWatch", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.started_at = datetime.now(UTC)
    app.include_router(router)
    app.mount("/static", StaticFiles(directory=settings.web_dir), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(settings.web_dir / "index.html")

    return app


app = create_app()
