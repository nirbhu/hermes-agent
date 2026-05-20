"""Token storage for Whoop API credentials.

Handles OAuth token persistence across platforms:
  - macOS: Keychain via `security` CLI
  - Linux/Windows: .env file fallback

Keychain uses an explicit path to handle profile sandboxes where
HOME resolves to a sandbox directory. See hermes-agent CONTRIBUTING.md
for the Keychain search list issue.

Service name: whoop-api
Keychain path: /Users/nirbhayshah/Library/Keychains/login.keychain-db (macOS)
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path

KEYCHAIN_SERVICE = "whoop-api"
KEYCHAIN_ACCOUNT = "whoop-tokens"
MACOS_KEYCHAIN_PATH = "/Users/nirbhayshah/Library/Keychains/login.keychain-db"

TOKEN_FIELDS = ("access_token", "refresh_token", "expires_at")


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _keychain_available() -> bool:
    """Check if `security` CLI exists and the login keychain is accessible."""
    if not _is_macos():
        return False
    try:
        result = subprocess.run(
            ["security", "show-keychain-info", MACOS_KEYCHAIN_PATH],
            capture_output=True, text=True, timeout=5,
        )
        # show-keychain-info returns 0 if the keychain exists and is accessible
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def load_tokens() -> dict[str, str | float] | None:
    """Load stored tokens. Returns None if no tokens exist.

    Tries Keychain first (macOS), then .env fallback.
    """
    if _keychain_available():
        return _load_from_keychain()
    return _load_from_env_file()


def save_tokens(access_token: str, refresh_token: str, expires_at: float) -> None:
    """Persist tokens. Keychain on macOS, .env file elsewhere."""
    data = {"access_token": access_token, "refresh_token": refresh_token,
            "expires_at": expires_at}
    if _is_macos():
        _save_to_keychain(data)
    else:
        _save_to_env_file(data)


def clear_tokens() -> None:
    """Remove stored tokens from Keychain or .env file."""
    if _is_macos():
        _clear_from_keychain()
    else:
        _clear_from_env_file()


# -- Keychain (macOS) --

def _load_from_keychain() -> dict[str, str | float] | None:
    """Read tokens from macOS Keychain using explicit keychain path."""
    try:
        result = subprocess.run(
            ["security", "find-generic-password",
             "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT,
             "-w", MACOS_KEYCHAIN_PATH],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout.strip())
        if all(k in data for k in TOKEN_FIELDS):
            return data
    except (json.JSONDecodeError, subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _save_to_keychain(data: dict) -> None:
    """Delete old entry (if any) then add new one to Keychain."""
    _clear_from_keychain()
    # Use subprocess with heredoc-style stdin for the password (JSON blob)
    password = json.dumps(data)
    # macOS security add-generic-password reads -w from stdin when using -c
    subprocess.run(
        ["security", "add-generic-password",
         "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT,
         "-w", password,
         MACOS_KEYCHAIN_PATH],
        check=True, timeout=10,
    )


def _clear_from_keychain() -> None:
    """Delete Keychain entry. Ignore errors if it doesn't exist."""
    subprocess.run(
        ["security", "delete-generic-password",
         "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT,
         MACOS_KEYCHAIN_PATH],
        capture_output=True, timeout=10,
    )


# -- .env file fallback (Linux/Windows) --

def _env_file_path() -> Path:
    """Return path to the Whoop tokens .env file."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "whoop-api" / "tokens.json"


def _load_from_env_file() -> dict[str, str | float] | None:
    """Read tokens from JSON file on Linux/Windows."""
    path = _env_file_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if all(k in data for k in TOKEN_FIELDS):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _save_to_env_file(data: dict) -> None:
    """Write tokens to JSON file with 0600 permissions on Linux/Windows."""
    path = _env_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    # Restrict permissions (no-op on Windows)
    if platform.system() != "Windows":
        path.chmod(0o600)


def _clear_from_env_file() -> None:
    """Delete the tokens JSON file."""
    path = _env_file_path()
    if path.exists():
        path.unlink()