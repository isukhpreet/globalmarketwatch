# GlobalMarketWatch

A personal one-stop tool for global markets: macro indicators (yields, CPI, policy rates), live
prices, news and geopolitics, an event calendar, and my portfolio. Covers US, Japan, South Korea,
Europe and the UK. Alerts go to Telegram, and Claude writes daily briefings.

> Decision-support only, not financial advice.

**Status:** Phase 1 of 9 complete (v0.1.0). See [docs/ROADMAP.md](docs/ROADMAP.md).

## Try it in the browser (nothing to install)
1. On GitHub: **Code → Codespaces → Create codespace on main**.
2. Wait for the setup to finish (first time ~2 minutes). The app starts automatically in a
   terminal panel named **Run GlobalMarketWatch**, and the dashboard opens in a preview pane
   inside the codespace.
3. You'll see the **system status** page: app health, background jobs, integrations and the core
   watchlist.

**To open the dashboard in a full browser tab:** click the **antenna icon** in the blue status bar
at the bottom (it shows the number of forwarded ports) → hover over port **8000** → click the
**globe icon**.

**If the dashboard doesn't appear**
- The app isn't running: **☰ menu → Terminal → Run Task… → Run GlobalMarketWatch**.
- VS Code asked "Allow automatic tasks?": choose **Allow**, so the app starts by itself next time.
- Check the **Run GlobalMarketWatch** terminal for error messages.

Stop the codespace when you're done (**Codespaces → Stop**) to save your free monthly hours.

## How it's built
- One Python app (FastAPI web server + background scheduler) and a SQLite database
- HTML dashboard with no build step
- Free data sources only; API keys live in `.env` (never committed). See `.env.example`

| Folder | Contents |
|---|---|
| `app/core` | Settings, logging, instrument registry |
| `app/storage` | Database schema and helpers |
| `app/collectors` | Price, macro and news collectors (phases 2, 4, 5) |
| `app/watchlist` | Dynamic watchlist manager (phase 4) |
| `app/portfolio` | Trading 212 API / CSV / manual portfolio (phase 8) |
| `app/alerts` | Alert rules and Telegram (phase 6) |
| `app/analyst` | Claude bridge and briefings (phase 9) |
| `app/api` | JSON API |
| `web/` | Dashboard pages |
| `config/` | Watchlist, series, calendar and alert config |
| `docs/` | Roadmap and decision log |

## Developer commands
```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000   # run
pytest -q                                   # tests
ruff check .                                # lint
```
