# Changelog

## [0.2.0] — 2026-11-18 — Phase 2: macro collectors
### Added
- Collector framework: shared HTTP client, retries with backoff (2s, 8s) for transient errors,
  per-series failure isolation, status reporting, API keys masked in every error message (#2)
- Release-time scheduling: each source polled on cron schedules (UK time) just after its usual
  release times, plus a first run a few seconds after start-up (#2)
- Series catalogue `config/series.yaml`: 44 series across US, euro area, UK, Japan, Korea,
  validated on start; `verified: false` marks codes not yet confirmed against live data (#3)
- Collectors: FRED (#4), US Treasury yield curve (#5), ECB Data Portal (#6), Bank of England and
  ONS (#7), Japan MoF JGB yields and Bank of Japan API (#8), Bank of Korea ECOS (#9)
- Revision detection: changed values are updated and flagged `revised`; first-seen time kept (#10)
- Year-on-year transform for index series (Korea CPI)
- `GET /api/macro/latest`, `POST /api/collectors/macro/{source}/run`
- Status page: macro data table (latest, change, period, source, first seen, unverified/revised
  tags) and "Run now" buttons; readable grouped error messages
- 49 new tests (65 total) using sample responses in each source's real format
### Fixed
- Duplicate dates in one response (e.g. overlapping Treasury year files) no longer crash a run

## [0.1.1] — 2026-11-18
### Fixed
- Codespaces: the app now starts in a visible VS Code task ("Run GlobalMarketWatch") when the
  codespace opens, replacing a detached background command that could die silently
- Codespaces: the dashboard opens in an in-editor preview pane (not blocked by pop-up blockers)
- README: how to open the dashboard in a full tab, plus troubleshooting

## [0.1.0] — 2026-11-18 — Phase 1: skeleton app + database
### Added
- Project layout for all modules (M0–M10) per architecture v1.1
- Settings from environment / `.env` with safe defaults; integration status without exposing secrets
- SQLite schema v1 (all tables from architecture §8), WAL mode, idempotent init
- Instrument registry and core watchlist (16 instruments across US, JP, KR, EU, UK, FX, commodities)
- FastAPI app with background scheduler heartbeat; `/api/health`, `/api/status`
- System status page (light/dark, mobile-friendly)
- Tests (14), GitHub Actions CI (ruff + pytest), Codespaces dev container
- README, CLAUDE.md, roadmap, decision log
