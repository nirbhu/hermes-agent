# Fleet — Multi-Agent Architecture for Hermes

This directory is the **template** for a multi-agent fleet setup. It contains skeleton directories, profile samples, config templates, and documentation — everything needed to bootstrap a fleet except your private data.

## How It Works

```
git clone → hermes setup → "set up fleet" → AI reads this README, copies skeletons,
                                         edits profiles, initializes kanban, starts gateway
```

You don't manually copy files or edit configs. You tell Hermes to set it up.

## Two Directories — Two Purposes

| Directory | Purpose | Git tracked | Lives at |
|-----------|---------|-------------|----------|
| `fleet/` (this dir) | Template/skeleton for fleet setup | Yes — only safe files | Inside the hermes-agent repo |
| `$HERMES_HOME/` | Your live runtime — profiles, cortex, kanban, sessions | No — `.gitignore` blocks all personal data | Outside the repo (e.g. `~/.hermes/` or `~/Workspace/.hermes/`) |

**Never edit files in `fleet/` for daily work.** Edit your live `$HERMES_HOME/` instead. `fleet/` is for contributing improvements back to the repo.

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/nirbhu/hermes-agent.git
cd hermes-agent
python3 -m venv venv
source venv/bin/activate
pip install -e '.[all]'
```

### 2. Set HERMES_HOME and run setup

```bash
export HERMES_HOME=~/.hermes   # or ~/Workspace/.hermes, or wherever you want
hermes setup                    # creates config.yaml, initializes state
```

### 3. Tell Hermes to set up the fleet

Open a chat with your Hermes instance and say:

> "Read the fleet README at the `fleet/` directory in the repo. Set up my fleet architecture: copy the cortex skeleton, create profiles from the samples, initialize the kanban board, and configure the dispatcher."

The AI will:
- Copy `fleet/cortex/` skeleton to `$HERMES_HOME/neo/cortex/`
- Create profiles from `fleet/profiles/samples/` into `$HERMES_HOME/profiles/`
- Copy `fleet/samples/config.yaml.sample` and `.env.sample` as starting points
- Initialize `kanban.db` and create the `fleet` board
- Set up the kanban dispatcher config (`max_spawn`, `dispatch_in_gateway`, etc.)

### 4. Add your credentials

Edit `$HERMES_HOME/.env` with your API keys and Telegram bot token. Edit each profile's `config.yaml` for model preferences.

### 5. Start the gateway

```bash
hermes gateway run    # starts Neo's gateway (includes kanban dispatcher)
```

Other agents get their own gateways in separate tmux sessions:
```bash
hermes -p mimir gateway run
hermes -p kachra-search gateway run
```

## Directory Structure

```
fleet/
├── README.md              ← This file
├── .gitignore             ← Blocks all personal data from git
├── cortex/                ← Knowledge base skeleton
│   ├── content/           ← Content pipeline (drafts → ready → published)
│   ├── neo-einstein/      ← Neo→Einstein handoff (unread/read/archive)
│   ├── neo-enigma/        ← Neo→Enigma handoff
│   ├── neo-hemingway/     ← Neo→Hemingway handoff
│   ├── neo-kachra/       ← Neo→Kachra handoff
│   ├── neo-mimir/         ← Neo→Mimir handoff
│   ├── einstein-mimir/    ← Einstein→Mimir handoff
│   ├── kachra-neo/        ← Kachra→Neo handoff
│   ├── hemingway-neo/     ← Hemingway→Neo handoff
│   ├── shared/            ← Shared data (agent-config.json)
│   └── ...                ← More dirs created by AI during setup
├── profiles/samples/      ← Agent profile templates
│   ├── bawa-neo/          ← Coordinator (config.yaml.sample, SOUL.md, .env.sample)
│   ├── einstein/          ← Research (config.yaml.sample, SOUL.md, .env.sample)
│   ├── enigma/            ← Code (config.yaml.sample, SOUL.md, .env.sample)
│   ├── mimir/             ← Learning (config.yaml.sample, SOUL.md, .env.sample)
│   ├── hemingway/         ← Writing (config.yaml.sample, SOUL.md, .env.sample)
│   └── kachra-search/    ← Search (config.yaml.sample, SOUL.md, .env.sample)
├── neo/
│   └── SESSION_CONTEXT.md ← Session state template (kanban-native architecture)
└── samples/
    ├── config.yaml.sample ← Main config with kanban dispatcher settings
    └── .env.sample         ← Environment variables template (API keys)
```

**What lives in `$HERMES_HOME/` (NOT in git):**

```
~/.hermes/ (or ~/Workspace/.hermes/)
├── config.yaml            ← Your live config (API keys, models, kanban settings)
├── .env                   ← Secrets (TELEGRAM_BOT_TOKEN, API keys)
├── kanban/                ← Task boards (kanban.db, workspaces)
├── profiles/
│   ├── bawa-neo/          ← Your actual profile (SOUL.md, memories, config.yaml, .env)
│   ├── einstein/          ← Einstein's runtime state
│   └── ...                 ← Other agents
├── neo/
│   ├── cortex/            ← Knowledge base with your actual data
│   │   ├── einstein-neo/  ← Einstein's research findings (private, gitignored)
│   │   ├── mimir-neo/     ← Mimir's progress reports (private, gitignored)
│   │   ├── shared/         ← user-profile.json, trend-alerts.json (private)
│   │   └── ...            ← More dirs with live data
│   └── SESSION_CONTEXT.md ← Live session state
├── scripts/               ← Cron scripts (tldr_scraper.py, etc.)
├── memories/              ← Persistent memories (USER.md, MEMORY.md)
└── cron/                  ← Scheduled jobs
```

## Architecture

| Layer | Tool | Purpose |
|-------|------|---------|
| **Deliverable files** | Filesystem (`cortex/`) | Research briefs, code reviews, markdown reports |
| **Agent comms** | Handoff dirs (`cortex/neo-{agent}/`) | Briefs, handoffs, context passing between agents |
| **Task monitoring** | Kanban (`kanban.db`) | Status signals, assignment, completion, notifications |
| **Knowledge** | agentmemory + ChromaDB | Persistent memory, semantic search, fast recall |
| **Source of truth** | Filesystem (`cortex/`) | Files are authoritative. agentmemory is search index. |

## Fleet Agents

| Agent | Role | Profile |
|-------|------|---------|
| Bawa Neo | Coordinator/partner | bawa-neo |
| Gyancho Einstein | Research/reasoning | einstein |
| Bhai Enigma | Implementation/code | enigma |
| Bantai Mimir | Learning co-pilot | mimir |
| Sasta Hemingway | Voice/writing | hemingway |
| Kachra Search | Search bot | kachra-search |

## Kanban Config

Only **one** profile should have `dispatch_in_gateway: true`. All others set it to `false`. This prevents race conditions where two dispatchers spawn the same task.

```yaml
# In $HERMES_HOME/config.yaml (or the dispatching profile's config.yaml)
kanban:
  dispatch_in_gateway: true      # Only Neo's gateway dispatches
  dispatch_interval_seconds: 60   # Tick rate
  max_spawn: 1                    # Max concurrent workers (prevents OOM on local LLM)
  failure_limit: 2               # Auto-block after 2 consecutive failures
  auto_decompose: false          # Don't auto-decompose triage tasks
  orchestrator_profile: "bawa-neo"  # Who decomposes triage tasks
  default_assignee: "bawa-neo"     # Fallback when no assignee matches
```

```yaml
# In other profiles (mimir, einstein, etc.)
kanban:
  dispatch_in_gateway: false     # No dispatching, just Telegram/message handling
```

## Key Conventions

- **No hard-coded paths.** Always use `$HERMES_HOME` or absolute paths. Never `~/.hermes/` in fleet-wide communications.
- **Task body = pointer + instructions.** Full brief lives in a file, body says "Full context at /path/to/brief.md"
- **Filesystem = source of truth.** agentmemory is a search index, not primary storage.
- **`--triage` for safe task creation.** `kanban create "title" --triage` parks tasks. Without `--triage`, tasks go to `ready` and get auto-dispatched immediately.
- **One dispatcher.** Only the dispatching profile's gateway runs the kanban dispatcher. All others set `dispatch_in_gateway: false`.

## What Gets Gitignored

The `.gitignore` blocks all personal data from being committed:
- `.env`, `config.yaml` (secrets and API keys)
- `profiles/*/sessions/`, `memories/`, `state.db` (runtime state)
- `kanban/`, `logs/`, `agents/` (task data, logs)
- `cortex/mimir/`, `cortex/einstein-neo/`, `cortex/fitness/` (research findings, personal data)
- `cortex/shared/user-profile.json`, `cortex/shared/trend-alerts.json` (personal info)

Only skeleton files (`.gitkeep`, `README.md`, `config.yaml.sample`, `SOUL.md` templates) get committed.

## For Contributors

If you improve a profile template, SOUL template, or config sample — edit it in `fleet/` and submit a PR. Your personal live data in `$HERMES_HOME/` stays local and private.