# Session Context — Fleet Bootstrap Template
# Copy to ~/.hermes/neo/SESSION_CONTEXT.md and customize.
# This file is read at session start by Neo to establish context.

# Session Context — Fleet

## Active Fleet

| Agent | Role | Model | Mode |
|-------|------|-------|------|
| Neo (Bawa) | Coordinator/partner | kimi-k2.6:cloud | Telegram gateway |
| Einstein (Gyancho) | Research/reasoning | gemma4:31b-cloud | Kanban worker |
| Mimir (Bantai) | Learning co-pilot | deepseek-v4-flash:cloud | Kanban + Telegram |
| Enigma (Bhai) | Implementation/code | deepseek-v4-flash:cloud | Kanban worker |
| Hemingway (Sasta) | Voice/writing | kimi-k2.6:cloud | Kanban worker |
| Kachra Search | Search bot | qwen3.5:cloud | Telegram gateway |

## Architecture (Kanban-Native)

- **Task dispatch:** `hermes kanban daemon` picks up ready tasks, spawns workers
- **Agent comms:** Handoff dirs (`cortex/neo-{agent}/`) for briefs + deliverables
- **Task monitoring:** Kanban comments for status signals, completion summaries
- **Knowledge:** agentmemory for semantic search, cortex/ files as source of truth
- **Source of truth pattern:** Write file first, then `memory_save` best effort. Read: `memory_smart_search` first, fall back to file if MCP down.

## Task Body Convention

Task body = pointer + instructions. Full brief in workspace or handoff dir.
Example: "Full context at cortex/neo-einstein/brief-2026-05-18.md. Read it before starting."

## Key Commands

```bash
hermes kanban create "Task title" --assign einstein --skills web,browser
hermes kanban list
hermes kanban show {task_id}
hermes kanban complete {task_id} --summary "Done. Result at cortex/einstein-neo/..."
hermes kanban daemon --interval 300
hermes kanban watch
hermes kanban boards list
```

## Persistent Daemons

| Service | Pattern | Start |
|---------|---------|-------|
| kanban daemon | launchd (auto-restart) | `hermes kanban daemon` |
| Mimir gateway | tmux | `HERMES_HOME=~/.hermes/profiles/mimir API_SERVER_PORT=8643 hermes -p mimir gateway run` |
| Kachra gateway | tmux | `HERMES_HOME=~/.hermes/profiles/kachra-search API_SERVER_PORT=8644 hermes -p kachra-search gateway run` |

## Kanban Boards

- `default` — general tasks
- `fleet` — fleet operations (agent spawning, research, builds)

## Handoff Directory Map

```
cortex/neo-mimir/      → Neo writes briefs for Mimir
cortex/mimir-neo/      → Mimir writes progress/reports for Neo
cortex/neo-einstein/   → Neo writes research requests for Einstein
cortex/einstein-neo/   → Einstein writes findings for Neo
cortex/einstein-mimir/ → Einstein writes research for Mimir to process
cortex/neo-enigma/     → Neo writes build tasks for Enigma
cortex/enigma-neo/     → Enigma writes build status for Neo
cortex/neo-hemingway/   → Neo writes content briefs for Hemingway
cortex/hemingway-neo/  → Hemingway writes drafts for Neo
cortex/neo-kachra/     → Neo writes search tasks for Kachra
cortex/kachra-neo/     → Kachra writes results for Neo
```

## Rules

- Never use `delegate_task` for fleet work — use kanban tasks
- Never update sprint.db/kanban task status directly — let the dispatcher handle it
- Always use absolute paths in fleet-wide communications
- Agentmemory must be verified operational before spawning fleet agents
- Token tracking for spawned agents comes from kanban `task_runs`
- Study tasks (STUDY-) are for the USER to read, not for agents to execute