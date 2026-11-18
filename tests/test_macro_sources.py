"""Each source parses its real response format (issues #4–#9), and the runner keeps
sources and series independent (issue #2)."""

from datetime import date

import httpx
import pytest

from app.collectors.macro.catalogue import load_catalogue
from app.collectors.macro.runner import run_source
from app.collectors.macro.source import FetchContext
from app.core.config import PROJECT_ROOT
from app.storage.db import init_db, session
from tests import fixtures as fx

CAT = load_catalogue(PROJECT_ROOT / "config" / "series.yaml")


def mock_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def ctx(**kw) -> FetchContext:
    base = {"since": date(2025, 1, 1), "incremental": True, "api_key": "KEY123",
            "retry_delay": 0}
    base.update(kw)
    return FetchContext(**base)


def spec(key):
    return next(s for s in CAT.series if s.key == key)


# ── Individual sources ─────────────────────────────────────────────────────────

def test_fred():
    from app.collectors.macro.fred import FredSource
    seen = {}
    def h(req):
        seen.update(req.url.params)
        return httpx.Response(200, json=fx.FRED_CPI)
    out = FredSource(mock_client(h)).fetch([spec("US.CPI.YOY")], ctx())
    assert out["US.CPI.YOY"] == [("2026-08-01", 2.9), ("2026-09-01", 3.0), ("2026-10-01", None)]
    assert seen["series_id"] == "CPIAUCSL" and seen["units"] == "pc1"
    assert seen["api_key"] == "KEY123" and seen["observation_start"] == "2025-01-01"


def test_fred_error_payload_is_reported():
    from app.collectors.macro.fred import FredSource
    out = FredSource(mock_client(lambda r: httpx.Response(200, json=fx.FRED_ERROR))).fetch(
        [spec("US.CPI.YOY")], ctx())
    assert "does not exist" in str(out["US.CPI.YOY"])


def test_treasury_curve():
    from app.collectors.macro.treasury import TreasurySource
    specs = [spec("US.UST.10Y"), spec("US.UST.3M")]
    out = TreasurySource(mock_client(lambda r: httpx.Response(200, text=fx.TREASURY_CSV))).fetch(
        specs, ctx(since=date.today()))
    assert ("2026-11-17", 5.10) in out["US.UST.10Y"]
    assert ("2026-11-16", 4.34) in out["US.UST.3M"]


def test_ecb():
    from app.collectors.macro.ecb import EcbSource
    urls = []
    def h(req):
        urls.append(str(req.url))
        return httpx.Response(200, text=fx.ECB_CSV)
    out = EcbSource(mock_client(h)).fetch([spec("EU.HICP.YOY")], ctx())
    assert out["EU.HICP.YOY"] == [("2026-09-01", 2.1), ("2026-10-01", 2.2)]
    assert "/service/data/ICP/M.U2.N.000000.4.ANR" in urls[0]


def test_boe_batch():
    from app.collectors.macro.boe import BoeSource
    seen = {}
    def h(req):
        seen.update(req.url.params)
        return httpx.Response(200, text=fx.BOE_CSV)
    out = BoeSource(mock_client(h)).fetch([spec("UK.BANKRATE"), spec("UK.GILT.10Y")], ctx())
    assert out["UK.BANKRATE"][0] == ("2026-10-01", 3.75)
    assert out["UK.GILT.10Y"][1] == ("2026-10-02", 5.354)
    assert seen["SeriesCodes"] == "IUDBEDR,IUDMNZC" and seen["Datefrom"] == "01/Jan/2025"


def test_ons_filters_by_since():
    from app.collectors.macro.ons import OnsSource
    out = OnsSource(mock_client(lambda r: httpx.Response(200, json=fx.ONS_JSON))).fetch(
        [spec("UK.CPI.YOY")], ctx(since=date(2026, 1, 1)))
    assert out["UK.CPI.YOY"] == [("2026-01-01", 3.0)]


def test_mof_current_and_history():
    from app.collectors.macro.mof import MofSource
    def h(req):
        body = fx.MOF_HISTORY_CSV if "historical" in str(req.url) else fx.MOF_CSV
        return httpx.Response(200, content=body.encode())
    src = MofSource(mock_client(h))
    out = src.fetch([spec("JP.JGB.10Y")], ctx(since=date(2026, 1, 1), incremental=False))
    assert out["JP.JGB.10Y"] == [("2026-10-30", 2.79), ("2026-11-02", 2.817),
                                 ("2026-11-04", 2.855)]
    out2 = src.fetch([spec("JP.JGB.10Y")], ctx(since=date(2026, 1, 1), incremental=True))
    assert out2["JP.JGB.10Y"][0] == ("2026-11-02", 2.817)


def test_boj():
    from app.collectors.macro.boj import BojSource
    seen = {}
    def h(req):
        seen.update(req.url.params)
        return httpx.Response(200, json=fx.BOJ_JSON)
    out = BojSource(mock_client(h)).fetch([spec("JP.CALLRATE")], ctx())
    assert out["JP.CALLRATE"] == [("2026-11-04", 0.727), ("2026-11-05", 0.728),
                                  ("2026-11-06", None)]
    assert seen["db"] == "FM01" and seen["code"] == "STRDCLUCON" and seen["startDate"] == "202501"


def test_ecos_and_no_data_and_bad_key():
    from app.collectors.macro.ecos import EcosSource
    paths = []
    def h(req):
        paths.append(req.url.path)
        if "901Y009" in req.url.path:
            return httpx.Response(200, json=fx.ECOS_CPI)
        if "817Y002" in req.url.path:
            return httpx.Response(200, json=fx.ECOS_NO_DATA)
        return httpx.Response(200, json=fx.ECOS_BASERATE)
    out = EcosSource(mock_client(h)).fetch(
        [spec("KR.BASERATE"), spec("KR.CPI.YOY"), spec("KR.KTB.10Y")], ctx())
    assert out["KR.BASERATE"][1] == ("2025-02-01", 2.75)
    assert out["KR.CPI.YOY"][2] == ("2026-01-01", 118.03)
    assert out["KR.KTB.10Y"] == []
    assert "/KEY123/json/en/1/100000/722Y001/M/202501/" in paths[0]
    assert paths[0].endswith("/0101000")
    bad = EcosSource(mock_client(lambda r: httpx.Response(200, json=fx.ECOS_BAD_KEY))).fetch(
        [spec("KR.BASERATE")], ctx())
    assert "INFO-100" in str(bad["KR.BASERATE"])


# ── Runner ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def db_settings(settings):
    init_db(settings.db_path)
    from app.collectors.macro.catalogue import seed_series
    with session(settings.db_path) as conn:
        seed_series(conn, CAT)
    return settings


def _status(settings, name):
    with session(settings.db_path) as conn:
        return dict(conn.execute("SELECT * FROM collector_status WHERE name=?",
                                 (name,)).fetchone())


def test_runner_skips_source_without_key(db_settings):
    res = run_source("fred", CAT, db_settings, client=mock_client(lambda r: 1 / 0))
    assert "GMW_FRED_API_KEY" in res.skipped
    st = _status(db_settings, "macro.fred")
    assert st["last_success"] is None and st["last_error"] is None
    assert "GMW_FRED_API_KEY" in st["detail"]


def test_runner_stores_transforms_and_isolates_failures(db_settings):
    db_settings.bok_ecos_api_key = "SECRETKEY"
    def h(req):
        if "901Y009" in req.url.path:
            return httpx.Response(200, json=fx.ECOS_CPI)
        if "010200000" in req.url.path:       # KTB 3y: server error on every attempt
            return httpx.Response(503, text=f"upstream down for {req.url.path}")
        return httpx.Response(200, json=fx.ECOS_BASERATE)
    res = run_source("ecos", CAT, db_settings, client=mock_client(h), retry_delay=0)
    assert set(res.ok) == {"KR.BASERATE", "KR.CPI.YOY", "KR.KTB.10Y"}
    assert set(res.failed) == {"KR.KTB.3Y"}
    st = _status(db_settings, "macro.ecos")
    assert st["last_success"] and st["last_error"]
    assert "SECRETKEY" not in st["last_error_msg"] and "***" in st["last_error_msg"]
    with session(db_settings.db_path) as conn:
        cpi = conn.execute("SELECT obs_date, value FROM macro_obs WHERE series_key='KR.CPI.YOY'"
                           " ORDER BY obs_date").fetchall()
    assert [tuple(r) for r in cpi] == [("2026-01-01", 2.63), ("2026-02-01", 2.51)]


def test_runner_second_run_is_incremental_and_counts_revisions(db_settings):
    calls = []
    def h(req):
        calls.append(req.url.params.get("startPeriod"))
        body = fx.ECB_CSV if len(calls) <= 7 else fx.ECB_CSV.replace("2026-10,2.2", "2026-10,2.3")
        return httpx.Response(200, text=body)
    first = run_source("ecb", CAT, db_settings, client=mock_client(h), retry_delay=0)
    assert first.new > 0 and first.revised == 0
    second = run_source("ecb", CAT, db_settings, client=mock_client(h), retry_delay=0)
    assert second.new == 0 and second.revised == len(CAT.for_source("ecb"))
    assert calls[-1] > calls[0]       # incremental window starts later than the backfill


def test_source_crash_never_raises(db_settings):
    def h(req):
        raise httpx.ConnectError("network unreachable")
    res = run_source("boe", CAT, db_settings, client=mock_client(h), retry_delay=0)
    assert not res.ok and len(res.failed) == len(CAT.for_source("boe"))
    assert "network unreachable" in _status(db_settings, "macro.boe")["last_error_msg"]


def test_group_errors():
    from app.collectors.macro.runner import group_errors
    assert group_errors({"A": "E1", "B": "E1"}) == "E1 (all 2 series)"
    assert group_errors({"A": "E1"}) == "A: E1"
    assert group_errors({"A": "E1", "B": "E2", "C": "E1"}) == "A, C: E1; B: E2"


def test_treasury_multi_year_overlap_is_stored_once(db_settings):
    """Regression: the same rows returned for two years crashed the whole run."""
    client = mock_client(lambda r: httpx.Response(200, text=fx.TREASURY_CSV))
    res = run_source("treasury", CAT, db_settings, client=client, retry_delay=0)
    assert len(res.ok) == len(CAT.for_source("treasury")) and not res.failed
    assert res.new == 2 * len(res.ok)
