#!/usr/bin/env python3
"""
Notification System Installer for Hermes CLI
Applies notification system patch to cli.py cleanly.
"""

import re
import sys
from pathlib import Path

# Read the file
cli_path = Path.home() / ".hermes" / "hermes-agent" / "cli.py"
content = cli_path.read_text()

# Check if already patched
if "_notification_queue: deque" in content:
    print("Notification system already installed!")
    sys.exit(0)

print("Installing notification system...")

# 1. Add imports after existing imports
import_section = """from pathlib import Path
from datetime import datetime"""

new_import_section = """from pathlib import Path
from collections import deque
from datetime import datetime"""

content = content.replace(import_section, new_import_section)
print("✓ Added deque import")

# 2. Add notification state in __init__
# Find the background_tasks section
old_bg_tasks = """        # Background task tracking: {task_id: threading.Thread}
        self._background_tasks: Dict[str, threading.Thread] = {}
        self._background_task_counter = 0"""

new_bg_tasks = """        # Background task tracking: {task_id: threading.Thread}
        self._background_tasks: Dict[str, threading.Thread] = {}
        self._background_task_counter = 0

        # Notification system for inter-agent communication
        self._notification_queue: deque = deque(maxlen=10)
        self._notification_watcher: Optional[threading.Thread] = None
        self._notification_watcher_started = False
        self._notifications_unread = 0"""

content = content.replace(old_bg_tasks, new_bg_tasks)
print("✓ Added notification state")

# 3. Add _start_notification_watcher method after _invalidate
# Find the _invalidate method and add watcher after it
watcher_method = '''

    def _start_notification_watcher(self):
        """Start filesystem watcher for notifications from other agents/channels."""
        if self._notification_watcher_started:
            return

        def watch_notifications():
            import json
            watch_path = Path.home() / ".hermes" / "neo" / "notifications"
            watch_path.mkdir(parents=True, exist_ok=True)

            while True:
                try:
                    # Check every 1 second
                    time.sleep(1)

                    # Look for new notification files
                    for f in watch_path.glob("*.json"):
                        try:
                            with open(f) as fp:
                                notification = json.load(fp)

                            # Check TTL
                            age = time.time() - notification.get("timestamp", 0)
                            if age > notification.get("ttl", 300):
                                f.unlink()
                                continue

                            # Add to queue
                            self._notification_queue.append(notification)
                            self._notifications_unread += 1

                            # Trigger UI refresh
                            self._invalidate(min_interval=0.1)

                            # Delete processed file
                            f.unlink()
                        except Exception:
                            pass  # Corrupted file, skip

                except Exception:
                    pass  # Keep watcher alive

        self._notification_watcher = threading.Thread(
            target=watch_notifications,
            daemon=True,
            name="notification-watcher"
        )
        self._notification_watcher.start()
        self._notification_watcher_started = True

'''

# Find where to insert - after _invalidate method
invalidate_end = '''        now = time.monotonic()
        if hasattr(self, "_app") and self._app and (now - self._last_invalidate) >= min_interval:
            self._last_invalidate = now
            self._app.invalidate()'''

content = content.replace(invalidate_end, invalidate_end + watcher_method)
print("✓ Added watcher method")

# 4. Add watcher start call after status bar creation
# Find the status bar creation
status_bar_creation = '''        status_bar = ConditionalContainer(
            Window(
                content=FormattedTextControl(lambda: cli_ref._get_status_bar_fragments()),
                height=1,
                # Prevent fragments that overflow the terminal width from
                # wrapping onto a second line, which causes the status bar to
                # appear duplicated (one full + one partial row) during long
                # sessions, especially on SSH where shutil.get_terminal_size
                # may return stale or fallback values (especially on SSH) that differ from what prompt_toolkit\'s own output object has been using.
                wrap_lines=False,
            ),
            filter=Condition(lambda: cli_ref._status_bar_visible),
        )'''

new_status_bar = '''        status_bar = ConditionalContainer(
            Window(
                content=FormattedTextControl(lambda: cli_ref._get_status_bar_fragments()),
                height=1,
                wrap_lines=False,
            ),
            filter=Condition(lambda: cli_ref._status_bar_visible),
        )

        # Start notification watcher for inter-agent communication
        self._start_notification_watcher()'''

content = content.replace(status_bar_creation, new_status_bar)
print("✓ Added watcher start call")

# 5. Modify _get_status_bar_fragments to include notification badge
# This is more complex - we need to modify the fragment building
# Find the snapshot building area

# For now, let's add a helper method that modifies the fragments
# We'll insert this before _get_status_bar_fragments

notification_helper = '''
    def _get_notification_badge(self) -> str:
        """Return notification badge string for status bar if unread notifications exist."""
        if self._notifications_unread <= 0:
            return ""

        # Clear badge when user is actively typing (prompt started)
        if getattr(self, "_prompt_start_time", None) is not None:
            self._notifications_unread = 0
            return ""

        if self._notifications_unread == 1:
            return "📱 1 │ "
        return f"📱 {self._notifications_unread} │ "

'''

# Insert before _get_status_bar_fragments
old_get_status = '''    def _get_status_bar_fragments(self):
        if not self._status_bar_visible or getattr(self, \'_model_picker_state\', None):'''

new_get_status = notification_helper + '''    def _get_status_bar_fragments(self):
        if not self._status_bar_visible or getattr(self, \'_model_picker_state\', None):'''

content = content.replace(old_get_status, new_get_status)
print("✓ Added notification badge helper")

# Now modify where the fragments are built
# Find the "frags = [" lines and add badge at start
# For the wide case (default):

# Look for the pattern where frags is built
old_frags = '''                    frags = [
                        ("class:status-bar", " ⚕ "),
                        ("class:status-bar-strong", snapshot["model_short"]),'''

new_frags = '''                    notification_badge = self._get_notification_badge()
                    frags = [
                        ("class:status-bar", f" ⚕ {notification_badge}"),
                        ("class:status-bar-strong", snapshot["model_short"]),'''

content = content.replace(old_frags, new_frags)
print("✓ Modified status bar fragments")

# Write back
cli_path.write_text(content)
print("\n✅ Notification system installed successfully!")
print("\nTo test:")
print("  cd ~/.hermes/hermes-agent")
print("  python -c \"from hermes_cli.skills.notification_system import notify_cli; notify_cli('test', 'Hello!')\"")
