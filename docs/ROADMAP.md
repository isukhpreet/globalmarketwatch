# Roadmap

One GitHub milestone per phase; each `- [ ]` line is one GitHub issue.
Architecture reference: Claude project doc `architecture/GlobalMarketWatch-Architecture.md` (v1.1).

## Phase 1 — Skeleton app + database (M0, M1) · v0.1.0
- [x] Repository layout, README, CLAUDE.md, decision log
- [x] Settings from environment / `.env` with safe defaults (M0)
- [x] Logging setup (M0)
- [x] SQLite schema v1 with all tables from architecture §8, WAL mode (M1)
- [x] Instrument registry + core watchlist config, seeded on start (M0/M10 seed)
- [x] FastAPI app + scheduler heartbeat + `/api/health`, `/api/status`
- [x] System status page in the browser
- [x] Tests + CI (ruff, pytest) + Codespaces dev container

**Done when:** app starts, schema created, core watchlist visible on the status page, CI green.

## Phase 2 — Macro collectors (M3) · v0.2.0 ✅ built (PR), live check pending
- [x] Collector framework: base class, retries/backoff, status reporting, release-time scheduling
- [x] Series catalogue `config/series.yaml`
- [x] FRED collector (US CPI, core CPI, PCE, payrolls, unemployment, GDP, Fed funds, 2y/10y/30y, 2s10s, breakevens)
- [x] US Treasury daily yield curve collector
- [x] ECB Data Portal collector (HICP, deposit rate, Bund yields)
- [x] Bank of England collector (Bank Rate, gilt yields) + ONS (CPI)
- [x] Bank of Japan / MoF collector (policy rate, JGB yields). Japan CPI moved to phase 3 (needs a free e-Stat appId)
- [x] Bank of Korea ECOS collector (base rate, CPI, KTB yields)
- [x] Revision detection on `macro_obs`

- [ ] Live check of all series in a Codespace with real keys (owner)

**Done when:** key series for US, euro area, UK, Japan and Korea stored and refreshing on schedule.

## Phase 3 — Dashboard: macro view (M5 v1) · v0.3.0
- [ ] Japan CPI collector via e-Stat (free appId)
- [ ] `/api/macro` endpoints (latest, history, by region)
- [ ] Macro dashboard page: yields, inflation, policy rates by region with charts
- [ ] Yield-curve chart (US, DE, UK, JP, KR)
- [ ] Freshness badges (timestamp + source on every value)
- [ ] Add-to-home-screen support (manifest, icons)

## Phase 4 — Live prices + dynamic watchlist (M2, M10) · v0.4.0
- [ ] Price collector framework + SSE live feed to the browser
- [ ] Finnhub WebSocket (US stocks/ETFs)
- [ ] Alpaca IEX WebSocket (fallback)
- [ ] IG streaming (indices, FX, bond futures, commodities)
- [ ] yfinance slow poller (JP/KR/EU stocks, fallback)
- [ ] Verify and complete symbol mappings in `config/core_watchlist.yaml`
- [ ] Watchlist manager: entry types, priority scoring, tier assignment, market hours
- [ ] Dynamic subscribe/unsubscribe on streams; minimum time per tier
- [ ] Dashboard: live watchlist with tier badges; pin/unpin search box

## Phase 5 — News + calendar (M4) · v0.5.0
- [ ] RSS collector (central banks, governments)
- [ ] Finnhub company/market news collector
- [ ] GDELT geopolitics collector
- [ ] Calendar: FRED release dates, ONS/Eurostat calendars, central bank meetings `config/calendar.yaml`
- [ ] Earnings calendar (Finnhub)
- [ ] Breaking-news pipeline: dedupe/clustering, impact score, severity levels
- [ ] Price-shock detector + "unexplained move" signal
- [ ] Auto-discovered watchlist entries from news/events
- [ ] Dashboard: calendar, news feed, breaking banner, chart markers

## Phase 6 — Alerts (M6) · v0.6.0
- [ ] Rule engine (`config/alerts.yaml`), cooldowns, quiet hours
- [ ] Telegram delivery
- [ ] Starter rules: moves, macro surprises, upcoming events, news severity, system health
- [ ] Alerts page on dashboard

## Phase 7 — Cloud deployment (M9) · v0.7.0
- [ ] Oracle Always Free VM setup guide + script (`deploy/`)
- [ ] systemd service, auto-restart
- [ ] Cloudflare Tunnel + Access login
- [ ] Encrypted nightly DB backup
- [ ] Health checks + collector-down alerts

## Phase 8 — Portfolio (M7) · v0.8.0
- [ ] Accounts + manual entry form
- [ ] Trading 212 CSV importer (history backfill, dedupe by order id)
- [ ] Trading 212 API importer (read-only), fallback to CSV
- [ ] Merge rules, mismatch check, per-source switches
- [ ] Valuation in GBP, P/L, allocation, concentration, dividends
- [ ] Holdings auto-join the watchlist
- [ ] Portfolio dashboard page

## Phase 9 — Claude analyst (M8) · v0.9.0
- [ ] `gmw-bridge` private repo + fine-grained token
- [ ] Data-pack exporter (morning, weekly, event snapshots)
- [ ] Briefing importer → dashboard + Telegram
- [ ] Template fallback briefing
- [ ] Claude scheduled tasks (morning, weekly) + `PROMPT.md`
- [ ] Claude watchlist suggestions → dashboard accept/dismiss

## v1.0.0 — all phases complete and running 24/7
