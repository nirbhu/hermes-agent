"""
Notification System for Inter-Agent Communication

Allows any agent (cron, telegram, subagents) to send notifications to the CLI agent,
displayed in the TUI status bar.

Architecture:
- Filesystem-based queue: ~/.hermes/neo/notifications/*.json
- CLI TUI has background watcher thread (1s polling)
- Status bar shows badge: 📱 N │
- Auto-clear on prompt submit

Usage:
    from hermes_cli.skills.notification_system import notify_cli
    
    notify_cli(
        source="telegram",
        title="New message from @user",
        priority="normal"
    )
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any


def notify_cli(
    source: str,
    title: str,
    priority: str = "normal",
    data: Optional[Dict[str, Any]] = None,
    ttl: int = 300  # 5 minute TTL
) -> bool:
    """
    Send notification to CLI agent.
    
    Args:
        source: 'telegram', 'cron', 'email', 'subagent', etc.
        title: Notification text (keep short for status bar)
        priority: 'normal' or 'urgent' (affects display)
        data: Optional extra data
        ttl: Seconds before auto-expire
        
    Returns:
        True if queued successfully, False otherwise
    """
    notification = {
        "id": f"{source}_{int(time.time() * 1000)}",
        "source": source,
        "title": title,
        "priority": priority,
        "data": data or {},
        "timestamp": time.time(),
        "ttl": ttl
    }
    
    try:
        watch_path = Path.home() / ".hermes" / "neo" / "notifications"
        watch_path.mkdir(parents=True, exist_ok=True)
        
        # Write atomically (temp + rename)
        temp_file = watch_path / f".tmp.{notification['id']}.json"
        final_file = watch_path / f"{notification['id']}.json"
        
        temp_file.write_text(json.dumps(notification, indent=2))
        temp_file.rename(final_file)
        
        return True
    except Exception:
        return False


def get_notification_path() -> Path:
    """Return the notification queue directory."""
    return Path.home() / ".hermes" / "neo" / "notifications"
