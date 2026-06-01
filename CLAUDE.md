# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CrStats is a Clash Royale clan statistics web app aimed at users worldwide: anyone can register and pick their own clan (multi-user, each user belongs to one clan, many different clans across all users). FastAPI backend + Vite/React frontend + a Discord bot (`backend/bot.py`) that shares the same models/services. The backend is deployed on a Hetzner Ubuntu server; the frontend builds to static files served by nginx alongside the API.

## Commands

### Frontend (`frontend/`)
- `npm run dev` — Vite dev server with `/api` proxy to the backend tunnel
- `npm run build` — production build (Vite emits to `dist/`)
- `npm run lint` — ESLint
- No tests configured.          

### Backend (`backend/`)
- Install: `pip install -r requirements.txt` inside `backend/venv`
- Local run: `uvicorn app.main:app --reload --port 8000` (rare — backend usually runs on the server)
- DB: SQLite at `backend/crstats.db`, schema is auto-created/migrated on app startup via `init_database()` + `ensure_schema()`. No Alembic.
- No tests configured.

### Deploy (server)
1. `git push` from local
2. SSH onto the server and run `bash deploy.sh` from `/root/Cr-Stats`
3. `deploy.sh` does: `git pull` → `pip install` → restart bot → restart `crstats-backend.service` → `npm run build` → copy dist to `/var/www/crstats/`

## Local Development Setup

Backend runs **on the server**, not locally. Frontend hits the backend through an SSH tunnel:

```
autossh -M 0 -f -N -L 8001:127.0.0.1:8000 root@<server>
```

`-M 0` is required (autossh prints usage without it). Tunnel often dies overnight — `ECONNREFUSED` in Vite logs is the symptom; restart the tunnel.

The Vite proxy (`frontend/vite.config.js`) maps `/api/*` → `localhost:8001/*` and **strips the `/api` prefix**. Backend routes are therefore declared without `/api` (e.g. `@router.get("/dashboard")`); the frontend always calls `apiRequest('/dashboard')` which becomes `/api/dashboard` → proxied to `localhost:8001/dashboard`.

## Architecture

### Multi-user model
Each `User` row has a `clan_tag` and `location_id`. Multiple users can belong to the same clan. Cached/snapshotted data is keyed by **clan_tag**, not user_id, so users in the same clan share data.

### Snapshot strategy for history charts
The Clash Royale API exposes only current state — no historical rankings. The `clan_ranking_snapshots` table stores daily rows per clan (trophy_rank, war_rank, clan_score, clan_war_trophies). `app/services/ranking_snapshots.py` runs as a startup background task (`snapshot_loop`) that runs hourly but inserts only one row per (clan_tag, date) — idempotent. `/rankings/history` also takes an inline snapshot for the requesting user's clan, so first-page-view always seeds data.

### Background tasks
Started in `app/main.py` `startup_event`:
- `poll_war_data_loop()` — refreshes the in-DB river-race state every 60s
- `snapshot_loop()` — daily ranking snapshots

### Frontend state convention
**All API state lives in `App.jsx`.** Pages receive data via props and never fetch on their own. Two poll intervals:
- `POLL_INTERVAL` = 5 min for live data (dashboard, members, war participants/performers)
- `RANKINGS_POLL_INTERVAL` = 30 min for historical/ranking data

This is deliberate — fetching in pages caused reload-on-page-switch which the user explicitly rejected. New data sources go through the same pattern: state + `loadAllData`/`loadRankings` in App.jsx, props down.

### Routing
Hash-based (`#/dashboard`, `#/war`, `#/rankings`, `#/profile`). `getPageFromHash()` in `App.jsx` is the source of truth. Login is gated by token presence in `localStorage`.

### Charts
`recharts` `ComposedChart` with **dual Y-axes**, right axis `reversed` so rank #1 is at the top (oben = gut for both score and rank lines). Rank-axis domain is dynamic with padding (`Math.max(1, min - padding)`) — never fixed to [1, 1000] because clans rank vastly differently.

## CR API Pitfalls (worth knowing before touching `services/clash_royale.py`)

- **`riverracelog[].standings[].clan.fame` is unreliable**: only correct for the final section of a season; other weeks return a tiny fragment value. Sum participant fame instead: `sum(p.fame for p in clan.participants)`.
- **`currentriverrace.clan.participants` may be empty** when the clan is in the `clans` standings list — fall back to `find_clan_by_tag(clans, tag).participants`.
- **`currentriverrace.participants` includes ex-members** who battled this race week. Cross-check with `/clans/{tag}/members` to filter when relevant (e.g., "missing today" lists).
- **No `periodEndTime`**: training/war end times must be derived from `riverracelog` `createdDate` patterns (race ends Mo ~09:36 UTC, war days Thu–Sun, training Mon–Wed — globally synchronized).
- **Tag normalization**: always uppercase + leading `#`, URL-encode `#` → `%23` before requests. Use `normalize_clan_tag()` / `normalize_player_tag()`.
- **CR_API_TOKEN whitelist**: API rejects with 401/403 unless the server's public IP is whitelisted in the CR developer portal.

## Conventions

- **Comments**: write WHY, not WHAT — module is currently very lightly commented and that's intentional. Add a comment when an external bug, surprising invariant, or workaround needs explaining (e.g., the `clan.fame` quirk note in `routes/rankings.py`).
- **No new schema tooling**: SQLite migrations are handled inline in `database.py`'s `ensure_schema()` (column-add via `ALTER TABLE`). For a new column, add it to the model and to `ensure_schema()`. New tables are picked up automatically by `Base.metadata.create_all`.
- **Bot vs. API share code**: `app/services/clash_royale.py` and `app/models.py` are imported by both `app/main.py` and `bot.py`. Don't introduce app-only or bot-only logic into shared services.
