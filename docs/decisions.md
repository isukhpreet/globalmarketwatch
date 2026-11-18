# Decision log

Short records of design choices: what was decided, why, and what was rejected.
Newest at the bottom. Full architecture: Claude project doc `architecture/GlobalMarketWatch-Architecture.md`.

| # | Date | Decision | Why | Alternatives rejected |
|---|---|---|---|---|
| D1 | 2026-11-18 | **Zero running cost** | Owner requirement | Paid data feeds, paid hosting |
| D2 | 2026-11-18 | **Browser front end + background Python service** | Needs 24/7 collection and alerts; no installer or executable for the owner | Pure HTML (stops when tab closes, CORS, exposed keys); desktop app |
| D3 | 2026-11-18 | **Custom HTML dashboard** (vanilla JS, SSE) | Live push updates, mobile-friendly, plain web page | Streamlit (no true push, weaker on mobile) |
| D4 | 2026-11-18 | **FastAPI + APScheduler in one process** | One thing to run and monitor | Separate worker processes / message queue (overkill) |
| D5 | 2026-11-18 | **SQLite in WAL mode** | Zero admin, single file, enough for one user | Postgres/TimescaleDB (upgrade path kept); DuckDB (single-writer limits with concurrent jobs) |
| D6 | 2026-11-18 | **Free price feeds: Finnhub WS, Alpaca IEX, IG streaming, yfinance** | Best free real-time coverage for US + global indices/FX | Paid exchange data; JP/KR/EU single stocks accepted at ~15-min delay |
| D7 | 2026-11-18 | **Portfolio from three sources** (T212 API, CSV, manual) merged with dedupe by order id | Convenience + resilience + whole-wealth view | API-only (beta risk), manual-only |
| D8 | 2026-11-18 | **Trading 212 key read-only + IP whitelist** | A leaked key cannot trade | Keys with order permission |
| D9 | 2026-11-18 | **Dynamic watchlist with tiered update rates** | Free streams cap at ~50–80 symbols | Fixed watchlist |
| D10 | 2026-11-18 | **AI via owner's existing Claude subscription**, files exchanged through a private GitHub repo | No extra cost; high quality | Claude API (paid), local LLM (weaker) |
| D11 | 2026-11-18 | **Develop in GitHub Codespaces, deploy to Oracle Always Free VM behind Cloudflare Access** | Nothing installed on the owner's laptop; free 24/7 hosting with login | Local-only; Streamlit Cloud (sleeps, no background jobs) |
| D12 | 2026-11-18 | **Full schema created in phase 1** | Later phases add data, not migrations | Incremental migrations per phase |
| D13 | 2026-11-18 | **One PR per phase when tasks are tightly coupled** (one commit per task, PR closes all the phase's issues) | Fewer reviews for the owner; tasks within a phase share code | One PR per issue (nine reviews for phase 2) |
| D14 | 2026-11-18 | **Macro sources:** Treasury CSV for the US curve (FRED for spreads/breakevens/macro); MoF CSV for JGBs; BoJ API (no key) for the call rate; ECB AAA curve as the daily euro benchmark + monthly German 10y; BoE for Bank Rate/gilts; ONS for UK macro; ECOS for Korea | Official, free, mostly keyless; only FRED and ECOS need keys | Paid aggregators; scraping web pages |
| D15 | 2026-11-18 | **`released_at` = first time we saw a value** | Collectors run just after release times, so this approximates publication time without a calendar | Hard-coding release times per series |
