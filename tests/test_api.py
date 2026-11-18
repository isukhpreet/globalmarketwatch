from app import __version__


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": __version__}


def test_status(client):
    d = client.get("/api/status").json()
    assert d["schema_version"] == 1
    assert d["base_currency"] == "GBP"
    assert len(d["watchlist"]) >= 10
    names = {c["name"] for c in d["collectors"]}
    assert {"system.startup", "system.heartbeat"} <= names


def test_status_never_exposes_secrets(settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    settings.finnhub_api_key = "SUPER-SECRET-KEY"
    with TestClient(create_app(settings)) as c:
        body = c.get("/api/status").text
    assert "SUPER-SECRET-KEY" not in body
    assert '"finnhub":true' in body.replace(" ", "")


def test_dashboard_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "GlobalMarketWatch" in r.text
    assert client.get("/static/style.css").status_code == 200


def test_macro_latest_lists_catalogue(client):
    d = client.get("/api/macro/latest").json()
    assert d["count"] >= 40 and d["with_data"] == 0
    keys = {s["series_key"] for s in d["series"]}
    assert "US.CPI.YOY" in keys and "KR.KTB.10Y" in keys
    assert d["series"][0]["region"] == "US"          # catalogue order: US, EU, UK, JP, KR
    ust = [s["series_key"] for s in d["series"] if s["series_key"].startswith("US.UST.")]
    assert ust[:3] == ["US.UST.1M", "US.UST.3M", "US.UST.6M"]
    unverified = {s["series_key"] for s in d["series"] if not s["verified"]}
    assert "JP.CALLRATE" in unverified


def test_run_macro_source_endpoint(client):
    assert client.post("/api/collectors/macro/nope/run").status_code == 404
    r = client.post("/api/collectors/macro/fred/run").json()   # no key in tests → skipped
    assert "GMW_FRED_API_KEY" in r["summary"]
    names = {c["name"] for c in client.get("/api/status").json()["collectors"]}
    assert "macro.fred" in names


def test_collectors_scheduled_when_enabled(settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    settings.collectors_enabled = True
    app = create_app(settings)
    with TestClient(app):
        jobs = {j.id for j in app.state.scheduler.get_jobs()}
        for j in list(jobs):
            if j.endswith(".startup"):
                app.state.scheduler.remove_job(j)   # don't hit the network in tests
    assert "macro.fred.0" in jobs and "macro.ecos.startup" in jobs
