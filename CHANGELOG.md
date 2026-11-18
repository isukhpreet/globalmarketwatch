# Changelog

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
