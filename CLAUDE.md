# Notes for Claude

Read this first in every session.

## Where things are
- Architecture (source of truth): Claude project doc `architecture/GlobalMarketWatch-Architecture.md`
- Progress tracker: Claude project doc `progress/GlobalMarketWatch-Progress.md`. Update it at the end of every session
- Roadmap / task list: `docs/ROADMAP.md`, mirrored as GitHub milestones (one per phase) and issues
- Decisions: `docs/decisions.md`. Add a row for every design choice

## How we work
- One issue → one branch (`phase-N/short-name`) → one PR that references the issue (`Closes #N`)
- The owner reviews and merges PRs. Don't push directly to `main` after the initial commit
- Every PR: tests added or updated, `ruff check .` and `pytest -q` pass, CHANGELOG entry
- Tag `vX.Y.0` when a phase's "done when" checks pass

## Rules
- **Never commit secrets.** Keys live only in `.env` (git-ignored). `.env.example` lists names only
- Never ask the owner to paste keys into chat
- Trading 212 integration is **read-only**. Never call order endpoints
- Every displayed value carries timestamp + source
- Collectors must fail independently and report to `collector_status`
- The analyst explains and flags risks; it never issues buy/sell instructions
- Keep the cost at zero: free tiers only unless the owner opts in

## Code conventions
- Python 3.12, FastAPI, APScheduler, SQLite (WAL), stdlib `sqlite3`
- Settings via `app/core/config.py` (env prefix `GMW_`)
- DB access via `app/storage/db.session()`. Timestamps are ISO-8601 UTC strings (`utcnow()`)
- Front end: plain HTML/CSS/vanilla JS in `web/`, no build step
- Line length 100, ruff rules E,F,I,B,UP
