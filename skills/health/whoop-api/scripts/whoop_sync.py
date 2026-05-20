#!/usr/bin/env python3
"""Whoop API sync tool — pull fitness data from Whoop via OAuth2.

Usage:
    python whoop_sync.py setup      # First-time OAuth authentication
    python whoop_sync.py pull        # Pull data from all endpoints
    python whoop_sync.py refresh     # Refresh access token manually
    python whoop_sync.py daemon      # Continuous sync on interval

Options:
    --interval N     Seconds between pulls (daemon mode, default: 1800)
    --data-dir PATH  Output directory (default: ./whoop_data)
    --date DATE      Pull specific date YYYY-MM-DD (default: yesterday)
    -h, --help       Show this help message
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from whoop_client import WhoopClient
from whoop_endpoints import all_endpoints, get_endpoint
from whoop_oauth import start_server
from whoop_storage import KEYCHAIN_SERVICE, load_tokens, save_tokens


def cmd_setup(args: argparse.Namespace) -> None:
    """Run the OAuth flow to authenticate with Whoop."""
    print("Starting Whoop OAuth2 setup...")
    print("A browser window will open. Authorize the app and come back here.")
    start_server()


def cmd_pull(args: argparse.Namespace) -> None:
    """Pull data from all Whoop endpoints and save to disk."""
    client = WhoopClient(data_dir=args.data_dir)
    results = client.pull_all(date=args.date)

    date_str = args.date or (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    output_dir = client.save_data(results, date=date_str)

    total = sum(len(v) for v in results.values())
    print(f"\nPulled {total} total records to {output_dir}")


def cmd_refresh(args: argparse.Namespace) -> None:
    """Manually refresh the Whoop access token."""
    client = WhoopClient(data_dir=args.data_dir)
    # _refresh_if_needed() is called automatically on next request,
    # but we force it here by creating a client and making a test call
    try:
        client._refresh_if_needed()
        print("Token refreshed successfully.")
    except Exception as e:
        print(f"Token refresh failed: {e}")
        print("Run `whoop_sync.py setup` to re-authenticate.")
        sys.exit(1)


def cmd_daemon(args: argparse.Namespace) -> None:
    """Run continuous sync on an interval."""
    interval = args.interval
    print(f"Starting Whoop daemon (interval: {interval}s)")
    print(f"Data directory: {args.data_dir}")
    print("Press Ctrl+C to stop.\n")

    # Handle graceful shutdown
    running = True

    def signal_handler(signum, frame):
        nonlocal running
        print("\nShutting down gracefully...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while running:
        try:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"[{timestamp}] Starting pull...")
            client = WhoopClient(data_dir=args.data_dir)
            results = client.pull_all(date=args.date)

            date_str = args.date or (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            output_dir = client.save_data(results, date=date_str)

            total = sum(len(v) for v in results.values())
            print(f"[{timestamp}] Pulled {total} records to {output_dir}")
        except Exception as e:
            print(f"[{timestamp}] Error: {e}")

        if running:
            print(f"Next pull in {interval}s...\n")
            time.sleep(interval)

    print("Daemon stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Whoop API sync tool — pull fitness data via OAuth2",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # setup
    sub_setup = subparsers.add_parser("setup", help="Authenticate with Whoop (first-time)")
    sub_setup.set_defaults(func=cmd_setup)

    # pull
    sub_pull = subparsers.add_parser("pull", help="Pull data from all endpoints")
    sub_pull.add_argument("--date", help="Date to pull (YYYY-MM-DD, default: yesterday)")
    sub_pull.add_argument("--data-dir", default="./whoop_data", help="Output directory")
    sub_pull.set_defaults(func=cmd_pull)

    # refresh
    sub_refresh = subparsers.add_parser("refresh", help="Refresh access token")
    sub_refresh.add_argument("--data-dir", default="./whoop_data", help="Output directory")
    sub_refresh.set_defaults(func=cmd_refresh)

    # daemon
    sub_daemon = subparsers.add_parser("daemon", help="Continuous sync on interval")
    sub_daemon.add_argument("--interval", type=int, default=1800,
                           help="Seconds between pulls (default: 1800)")
    sub_daemon.add_argument("--date", help="Date to pull (YYYY-MM-DD, default: yesterday)")
    sub_daemon.add_argument("--data-dir", default="./whoop_data", help="Output directory")
    sub_daemon.set_defaults(func=cmd_daemon)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()