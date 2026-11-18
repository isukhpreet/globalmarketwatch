"""Collector framework, catalogue and revision detection (issues #2, #3, #10)."""

import httpx
import pytest

from app.collectors.base import parse_period, retry, to_float
from app.collectors.macro import SOURCES
from app.collectors.macro.catalogue import Catalogue, load_catalogue
from app.collectors.macro.store import apply_transform, upsert_observations
from app.core.config import PROJECT_ROOT
from app.storage.db import init_db, session


@pytest.mark.parametrize("raw, iso", [
    ("2026-11-17", "2026-11-17"), ("2026-10", "2026-10-01"), ("2026-Q3", "2026-07-01"),
    ("2026Q4", "2026-10-01"), ("20261117", "2026-11-17"), ("202611", "2026-11-01"),
    (20261104, "2026-11-04"), ("2026", "2026-01-01"), ("11/17/2026", "2026-11-17"),
    ("2026/11/4", "2026-11-04"), ("R8.11.4", "2026-11-04"), ("H31.4.1", "2019-04-01"),
    ("2026 JAN", "2026-01-01"), ("2026 Q2", "2026-04-01"), ("01 Oct 2026", "2026-10-01"),
])
def test_parse_period(raw, iso):
    assert parse_period(raw) == iso


def test_parse_period_rejects_garbage():
    with pytest.raises(ValueError):
        parse_period("not a date")


@pytest.mark.parametrize("raw, val", [
    ("3.25", 3.25), (".", None), ("", None), ("NA", None), (None, None), (2, 2.0),
    ("1,234.5", 1234.5), ("abc", None),
])
def test_to_float(raw, val):
    assert to_float(raw) == val


def _status_error(code):
    req = httpx.Request("GET", "https://x")
    return httpx.HTTPStatusError("err", request=req, response=httpx.Response(code, request=req))


def test_retry_recovers_from_transient_errors():
    calls = []
    def fn():
        calls.append(1)
        if len(calls) < 3:
            raise _status_error(503)
        return "ok"
    assert retry(fn, attempts=3, base_delay=0) == "ok"
    assert len(calls) == 3


def test_retry_does_not_retry_client_errors():
    calls = []
    def fn():
        calls.append(1)
        raise _status_error(404)
    with pytest.raises(httpx.HTTPStatusError):
        retry(fn, attempts=3, base_delay=0)
    assert len(calls) == 1


# ── Catalogue ──────────────────────────────────────────────────────────────────

def test_real_catalogue_is_valid_and_covers_all_regions():
    cat = load_catalogue(PROJECT_ROOT / "config" / "series.yaml")
    assert {s.region for s in cat.series} >= {"US", "EU", "UK", "JP", "KR"}
    assert set(cat.sources) == set(SOURCES), "every source in config has an implementation"
    keys = {s.key for s in cat.series}
    assert {"US.CPI.YOY", "US.UST.10Y", "EU.HICP.YOY", "UK.BANKRATE", "JP.JGB.10Y",
            "KR.BASERATE"} <= keys


def _cat(**over):
    data = {
        "sources": {"fred": {"schedule": ["0 9 * * *"]}},
        "series": [{"key": "A", "name": "A", "region": "US", "frequency": "m",
                    "source": "fred", "source_id": "X"}],
    }
    data.update(over)
    return data


def test_catalogue_rejects_duplicates_unknown_sources_and_bad_cron():
    s = _cat()["series"][0]
    with pytest.raises(ValueError, match="Duplicate"):
        Catalogue.model_validate(_cat(series=[s, s]))
    with pytest.raises(ValueError, match="unknown sources"):
        Catalogue.model_validate(_cat(series=[{**s, "source": "nope"}]))
    with pytest.raises(ValueError):
        Catalogue.model_validate(_cat(sources={"fred": {"schedule": ["99 99 * * *"]}}))


# ── Transforms and revisions ───────────────────────────────────────────────────

def test_yoy_transform():
    obs = [("2025-01-01", 100.0), ("2025-02-01", 100.0), ("2026-01-01", 103.0),
           ("2026-02-01", None), ("2026-03-01", 101.0)]
    assert apply_transform(obs, "yoy") == [("2026-01-01", 3.0)]
    assert apply_transform(obs, "none") == obs


def test_upsert_detects_new_unchanged_and_revised(tmp_path):
    db = tmp_path / "m.sqlite"
    init_db(db)
    with session(db) as conn:
        conn.execute("""INSERT INTO macro_series(series_key, name, region, frequency, source,
                        source_id) VALUES ('K','K','US','m','fred','X')""")
        r1 = upsert_observations(conn, "K", [("2026-09-01", 3.0), ("2026-10-01", None)], "t1")
        r2 = upsert_observations(conn, "K", [("2026-09-01", 3.0), ("2026-10-01", 3.1)], "t2")
        r3 = upsert_observations(conn, "K", [("2026-09-01", 2.9)], "t3")
        row = conn.execute("SELECT * FROM macro_obs WHERE obs_date='2026-09-01'").fetchone()
    assert (r1.new, r1.revised) == (1, 0)          # None skipped
    assert (r2.new, r2.unchanged, r2.revised) == (1, 1, 0)
    assert (r3.new, r3.revised) == (0, 1)
    assert row["value"] == 2.9 and row["revised"] == 1
    assert row["released_at"] == "t1"              # first-seen time preserved


def test_upsert_handles_duplicate_dates_in_one_batch(tmp_path):
    db = tmp_path / "m.sqlite"
    init_db(db)
    with session(db) as conn:
        conn.execute("""INSERT INTO macro_series(series_key, name, region, frequency, source,
                        source_id) VALUES ('K','K','US','d','treasury','X')""")
        r = upsert_observations(conn, "K", [("2026-11-17", 5.1), ("2026-11-17", 5.2)], "t")
        v = conn.execute("SELECT value FROM macro_obs").fetchall()
    assert r.new == 1 and [x["value"] for x in v] == [5.2]
