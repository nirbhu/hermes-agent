---
name: notification-system
version: 1.0.0
description: Send notifications to CLI agent from any agent/channel
tools: []
---

# Notification System

Send notifications to the CLI agent's status bar from any agent, cron job, or external process.

## Usage

```python
from hermes_cli.skills.notification_system import notify_cli

notify_cli(
    source="telegram",
    title="New message from @user",
    priority="normal"  # or "urgent"
)
```

## Architecture

- **Queue**: Filesystem at `~/.hermes/neo/notifications/*.json`
- **Watcher**: Background thread in CLI TUI (1s polling)
- **Display**: Status bar badge `📱 N │`
- **Clear**: Auto-clears on next prompt submit

## Example Sources

- `telegram` - Telegram gateway messages
- `cron` - Cron job completions/failures
- `email` - Email worker notifications
- `subagent` - Background task completions

## Notification Lifecycle

1. Any agent calls `notify_cli()`
2. JSON file created in notification queue
3. CLI watcher spots file (within 1 second)
4. Badge appears in status bar
5. User submits prompt → Badge clears
6. Notification queued in memory (last 10)

## Priority Levels

- `normal` - Standard notification
- `urgent` - Highlighted in status bar

## Implementation Notes

- Uses atomic file writes (temp + rename) for safety
- TTL of 5 minutes (notifications auto-expire if not processed)
- No external dependencies (watchdog not required)
