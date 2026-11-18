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
