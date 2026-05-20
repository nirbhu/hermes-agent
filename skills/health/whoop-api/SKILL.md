---
name: whoop-api
description: Pull Whoop fitness data via OAuth2 API.
version: 1.0.0
author: Nirbhay Shah (nirbhayshah)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [whoop, fitness, health, api, oauth, wearable]
    related_skills: [fitness, fitness-coaching]
    requires_toolsets: [terminal]
---

# Whoop API Skill

Pull recovery, strain, sleep, and workout data from the Whoop API using OAuth2
authorization. Does not push data or modify Whoop settings — read-only access.

## When to Use

- User asks for Whoop data (recovery score, strain, sleep, HRV)
- Fitness or health coaching needs real wearable metrics
- Cron job needs to sync Whoop data for dashboards or analysis
- Don't use for: modifying Whoop settings, push notifications, or real-time streaming

## Prerequisites

- Whoop Developer App registered at [developer.whoop.com](https://developer.whoop.com)
- Environment variables:
  - `WHOOP_CLIENT_ID` — from your Whoop dev app
  - `WHOOP_CLIENT_SECRET` — from your Whoop dev app
- Python 3.10+ (uses `http.server` from stdlib for OAuth callback)
- `requests` library: `pip install requests`
- macOS: tokens stored in Keychain (service: `whoop-api`)
- Linux/Windows: tokens stored in `.env` as fallback

Set env vars in `.env`:

```bash
# Whoop API (skills/health/whoop-api)
# Register app at developer.whoop.com
# WHOOP_CLIENT_ID=your-client-id
# WHOOP_CLIENT_SECRET=your-client-secret
```

## How to Run

Invoke through the `terminal` tool:

```bash
# First-time setup: authenticate with Whoop
python scripts/whoop_sync.py setup

# Pull latest data from all endpoints
python scripts/whoop_sync.py pull

# Refresh tokens manually (rarely needed — auto-refreshes on pull)
python scripts/whoop_sync.py refresh

# Continuous sync every 30 minutes
python scripts/whoop_sync.py daemon --interval 1800
```

All commands run from the skill directory. Use absolute paths when calling from outside.

## Quick Reference

### CLI Commands

| Command | Description |
|---|---|
| `setup` | Start OAuth flow, open browser, store tokens |
| `pull` | Fetch all endpoints, save JSON to `whoop_data/{date}/` |
| `refresh` | Refresh access token if expired |
| `daemon` | Run pull on interval loop (default 1800s) |

### CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--interval N` | 1800 | Seconds between pulls (daemon mode) |
| `--data-dir PATH` | `./whoop_data` | Output directory for JSON files |

### API Endpoints

| Endpoint | Path | Key Data |
|---|---|---|
| Cycle | `/v2/cycle` | Strain, heart rate, kilojoules |
| Recovery | `/v2/recovery` | Recovery %, HRV, resting HR |
| Sleep | `/v2/activity/sleep` | Sleep stages, efficiency, debt |
| Workout | `/v2/activity/workout` | Strain by activity, duration |
| Body | `/v2/user/measurement/body` | Weight, height |
| Profile | `/v2/user/profile/basic` | User info |

### Data Output

```
whoop_data/
└── 2026-05-19/
    ├── cycle.json
    ├── recovery.json
    ├── sleep.json
    ├── workout.json
    ├── body.json
    └── profile.json
```

## Procedure

### 1. Register Whoop Developer App

1. Go to [developer.whoop.com](https://developer.whoop.com)
2. Create a new application
3. Set redirect URI to `http://localhost:8647/callback`
4. Select scopes: `read:recovery`, `read:cycles`, `read:sleep`, `read:workouts`, `read:body_measurement`, `read:profile`
5. Copy Client ID and Client Secret

### 2. Store Credentials

Add to your `.env` file:

```bash
WHOOP_CLIENT_ID=your-client-id
WHOOP_CLIENT_SECRET=your-client-secret
```

### 3. First-Time Authentication

```bash
python scripts/whoop_sync.py setup
```

Browser opens Whoop login. Authorize the app. Tokens are stored in Keychain
(macOS) or `.env` (Linux/Windows). The callback server runs on localhost:8647.

### 4. Pull Data

```bash
python scripts/whoop_sync.py pull
```

Fetches all endpoints for the current day. Data saved as JSON files in
`whoop_data/{date}/`. Access tokens are auto-refreshed if expired.

### 5. Set Up Scheduled Sync

Use the `cronjob` tool to schedule regular data pulls. See
`templates/cron-entry.yaml` for an example configuration.

## Pitfalls

- **Rate limit: 100 requests/minute.** Daemon mode defaults to 1800s intervals.
  Don't reduce below 60s — a single pull uses 6 requests (one per endpoint).
- **Token expiry: 1 hour.** Access tokens expire every 3600s. `pull` and
  `daemon` auto-refresh. If you get 401s, run `refresh` manually.
- **Keychain from agent profiles.** If running from a Hermes profile sandbox,
  Keychain needs the explicit path:
  `/Users/nirbhayshah/Library/Keychains/login.keychain-db`. The storage module
  handles this automatically.
- **OAuth callback port 8647.** Must be available during `setup`. If port is in
  use, the script will fail with a clear error — no silent hang.
- **No real-time data.** Whoop API is not a streaming API. Data appears after
  sync from the band to Whoop's servers. Typical delay: 5-15 minutes after
  activity ends.

## Verification

```bash
python scripts/whoop_sync.py pull && ls whoop_data/*/cycle.json
```

If a `cycle.json` file exists with valid JSON, the skill is working.