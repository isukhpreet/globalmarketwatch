"""Runs macro sources and schedules them (issue #2).

Each run: work out how far back to fetch → fetch with retries → transform → store with
revision detection → record status. Every source is independent: a failure is recorded
and never affects the others.
"""

from dataclasses import dataclass, field
from datetime import UTC, date, timedelta

import httpx
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.triggers.cron import CronTrigger

from app.collectors.base import make_client
from app.collectors.macro import SOURCES
from app.collectors.macro.catalogue import Catalogue, SeriesSpec
from app.collectors.macro.source import FetchContext
from app.collectors.macro.store import apply_transform, upsert_observations
from app.core.config import Settings
from app.core.logging import get_logger
from app.storage.db import record_status, session, utcnow

log = get_logger("gmw.macro")
REFETCH_DAYS = 400  # re-request ~13 months each run: catches revisions and feeds y/y transforms


@dataclass
class RunResult:
    source: str
    skipped: str = ""
    ok: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)
    new: int = 0
    revised: int = 0

    def summary(self) -> str:
        if self.skipped:
            return self.skipped
        total = len(self.ok) + len(self.failed)
        return f"{len(self.ok)}/{total} series ok · {self.new} new · {self.revised} revised"


def status_name(source: str) -> str:
    return f"macro.{source}"


def _since(conn, specs: list[SeriesSpec], lookback_years: int) -> tuple[date, bool]:
    """Full backfill if any series is empty; otherwise only the recent window."""
    full = date.today().replace(month=1, day=1) - timedelta(days=365 * lookback_years)
    latest = []
    for s in specs:
        row = conn.execute("SELECT MAX(obs_date) AS d FROM macro_obs WHERE series_key = ?",
                           (s.key,)).fetchone()
        if row["d"] is None:
            return full, False
        latest.append(date.fromisoformat(row["d"]))
    return max(full, min(latest) - timedelta(days=REFETCH_DAYS)), True


def run_source(source: str, cat: Catalogue, settings: Settings,
               client: httpx.Client | None = None, retry_delay: float = 2.0) -> RunResult:
    res = RunResult(source)
    spec = cat.sources[source]
    specs = cat.for_source(source)
    api_key = getattr(settings, spec.key) if spec.key else ""

    if spec.key and not api_key:
        res.skipped = f"Not configured: add GMW_{spec.key.upper()} to activate"
    elif not specs:
        res.skipped = "No series configured"
    if res.skipped:
        with session(settings.db_path) as conn:
            record_status(conn, status_name(source), ok=None, detail=res.skipped)
        return res

    with session(settings.db_path) as conn:
        since, incremental = _since(conn, specs, settings.macro_lookback_years)

    own_client = client is None
    client = client or make_client()
    try:
        results = SOURCES[source](client).fetch(
            specs, FetchContext(since, incremental, api_key, retry_delay))
    except Exception as e:  # defensive: sources should already capture per-series errors
        results = {s.key: e for s in specs}
    finally:
        if own_client:
            client.close()

    now = utcnow()
    with session(settings.db_path) as conn:
        for s in specs:
            r = results.get(s.key, KeyError("not returned by source"))
            if isinstance(r, Exception):
                res.failed[s.key] = _describe(r, api_key)
                continue
            try:
                up = upsert_observations(conn, s.key, apply_transform(r, s.transform), now)
            except Exception as e:  # bad data for one series must not lose the others
                res.failed[s.key] = _describe(e, api_key)
                continue
            res.ok.append(s.key)
            res.new += up.new
            res.revised += up.revised
        name = status_name(source)
        if res.ok:
            record_status(conn, name, ok=True, detail=res.summary())
        else:
            record_status(conn, name, ok=None, detail=res.summary())
        if res.failed:
            record_status(conn, name, ok=False, error=group_errors(res.failed))
    log.info("%s: %s%s", source, res.summary(),
             f" · failed: {', '.join(res.failed)}" if res.failed else "")
    return res


def group_errors(failed: dict[str, str]) -> str:
    """'ConnectError: x (all 11 series)' or 'A, B: err1; C: err2' — readable on the status page."""
    by_msg: dict[str, list[str]] = {}
    for key, msg in failed.items():
        by_msg.setdefault(msg, []).append(key)
    if len(by_msg) == 1:
        msg, keys = next(iter(by_msg.items()))
        if len(keys) > 1:
            return f"{msg} (all {len(keys)} series)"
    return "; ".join(f"{', '.join(keys)}: {msg}" for msg, keys in by_msg.items())


def _describe(e: Exception, secret: str) -> str:
    msg = f"{type(e).__name__}: {e}"
    if secret:
        msg = msg.replace(secret, "***")   # never leak API keys into logs or the status page
    return msg[:200]


def schedule_macro(scheduler: BaseScheduler, cat: Catalogue, settings: Settings,
                   run_now: bool = True) -> list[str]:
    """Add each source's cron jobs (UK time) plus an initial run shortly after start-up."""
    from datetime import datetime

    job_ids = []
    for i, (name, spec) in enumerate(cat.sources.items()):
        for j, expr in enumerate(spec.schedule):
            jid = f"macro.{name}.{j}"
            trigger = CronTrigger.from_crontab(expr, timezone=settings.timezone)
            scheduler.add_job(run_source, trigger,
                              args=[name, cat, settings], id=jid, replace_existing=True,
                              max_instances=1, coalesce=True, misfire_grace_time=3600)
            job_ids.append(jid)
        if run_now:
            scheduler.add_job(run_source, "date", args=[name, cat, settings],
                              id=f"macro.{name}.startup", replace_existing=True,
                              run_date=datetime.now(UTC) + timedelta(seconds=3 + 2 * i))
    return job_ids
