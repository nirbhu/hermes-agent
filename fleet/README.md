# Fleet — Multi-Agent System for Hermes

This directory contains the fleet configuration for running multiple specialized AI agents coordinated by a central orchestrator (Neo/Bawa).

## Quick Start

1. **Clone and install:**
   ```bash
   git clone https://github.com/nirbhu/hermes-agent.git
   cd hermes-agent
   python3 -m venv venv
   source venv/bin/activate
   pip install -e '.[all]'
   ```

2. **Set up HERMES_HOME:**
   ```bash
   export HERMES_HOME=~/.hermes  # or wherever you want
   hermes setup  # creates config.yaml
   ```

3. **Create profiles:**
   ```bash
   # For each agent, create a profile from the samples:
   cp -r fleet/profiles/samples/einstein ~/.hermes/profiles/einstein
   # Edit config.yaml with your API keys and model preferences
   ```

4. **Initialize kanban:**
   ```bash
   hermes kanban init
   hermes kanban boards create fleet
   hermes kanban boards switch fleet
   ```

5. **Set up cortex structure:**
   ```bash
   cp -r fleet/cortex/skeleton/* ~/.hermes/cortex/
   # Edit user-profile.json with your personal data
   ```

6. **Start the dispatcher:**
   ```bash
   hermes kanban daemon --interval 300
   ```

## Architecture

| Layer | Tool | Purpose |
|-------|------|---------|
| **Deliverable files** | Filesystem (`cortex/`) | Research briefs, code reviews, markdown reports |
| **Agent comms** | Handoff dirs (`cortex/neo-{agent}/`) | Briefs, handoffs, context passing between agents |
| **Task monitoring** | Kanban (`kanban.db`) | Status signals, assignment, completion, notifications |
| **Knowledge** | agentmemory + ChromaDB | Persistent memory, semantic search, fast recall |
| **Source of truth** | Filesystem (cortex/) | Files are authoritative. agentmemory is search index. |

## Fleet Agents

| Agent | Role | Model | Profile |
|-------|------|-------|---------|
| Bawa Neo | Coordinator/partner | kimi-k2.6:cloud | bawa-neo |
| Gyancho Einstein | Research/reasoning | gemma4:31b-cloud | einstein |
| Bhai Enigma | Implementation/code | deepseek-v4-flash:cloud | enigma |
| Bantai Mimir | Learning co-pilot | deepseek-v4-flash:cloud | mimir |
| Sasta Hemingway | Voice/writing | kimi-k2.6:cloud | hemingway |
| Kachra Search | Search bot | qwen3.5:cloud | kachra-search |

## Agent Communication

- **Kanban tasks** for background dispatch: `hermes kanban create "Do research" --assign einstein`
- **Handoff dirs** for briefs and deliverables: `cortex/neo-{agent}/` and `cortex/{agent}-neo/`
- **Telegram gateways** for live interactive work (Mimir, Kachra are persistent)
- **Task body** = pointer to brief file. Full context in workspace, not inline.

## Key Conventions

- `FLEET-` prefix in kanban for auto-dispatched tasks
- `AUDIT-` prefix for tasks that need human review before dispatch
- Body field always points to a file: "Full context at /path/to/brief.md"
- Filesystem = source of truth. agentmemory = search index.
- Profiles use `HERMES_HOME` env var, no hard-coded paths