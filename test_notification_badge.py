#!/usr/bin/env python3
"""
Test Notification Badge for Neo

Usage:
    python3 ~/.hermes/hermes-agent/test_notification_badge.py
    
Prerequisites:
    - Hermes CLI must be running in another terminal
    - Notification system must be installed (neo-features branch)

What it does:
    1. Sends a test notification via the notification system
    2. Notification appears in ~/.hermes/neo/notifications/
    3. Hermes watcher thread spots it (within 1 second)
    4. Badge appears in status bar: 📱 1 │
    
How to verify:
    - Look at Hermes status bar for "📱 1 │" badge
    - Badge auto-clears when you submit next prompt
"""

import sys
import time
from pathlib import Path

# Add hermes to path
sys.path.insert(0, str(Path.home() / ".hermes" / "hermes-agent"))

try:
    from hermes_cli.skills.notification_system import notify_cli
    
    print("🧪 Testing Neo Notification System...")
    print("=" * 50)
    
    # Send test notification
    result = notify_cli(
        source="test",
        title="🎉 Notification system is working!",
        priority="normal",
        data={"test": True, "timestamp": time.time()}
    )
    
    if result:
        print("✅ Notification sent successfully!")
        print("\n📱 Check your Hermes status bar - you should see:")
        print('   "⚕ 📱 1 │ ..." badge in the status bar')
        print("\n⌛ The badge will appear within 1 second")
        print("💡 Submit a prompt to clear the badge")
    else:
        print("❌ Failed to send notification")
        print("   Check that ~/.hermes/neo/notifications/ directory exists")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Make sure you're in the hermes-agent directory")
    print("   and the notification_system skill is installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
