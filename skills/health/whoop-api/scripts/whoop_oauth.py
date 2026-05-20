"""Whoop OAuth2 Authorization Code flow.

Starts a local HTTP server on port 8647 to catch the callback,
exchanges the auth code for tokens, and stores them via whoop_storage.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from whoop_storage import KEYCHAIN_SERVICE, save_tokens

AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
REDIRECT_PORT = 8647
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

SCOPES = [
    "read:recovery",
    "read:cycles",
    "read:sleep",
    "read:workouts",
    "read:body_measurement",
    "read:profile",
]


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles the OAuth redirect callback on localhost."""

    auth_code: str | None = None

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if "code" in params:
            OAuthCallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Authorization successful!</h1>"
                             b"<p>You can close this tab.</p>")
        elif "error" in params:
            error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<h1>Authorization failed: {error}</h1>".encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args) -> None:
        """Suppress default HTTP logging."""
        pass


def _get_client_credentials() -> tuple[str, str]:
    """Read WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET from environment."""
    client_id = os.environ.get("WHOOP_CLIENT_ID")
    client_secret = os.environ.get("WHOOP_CLIENT_SECRET")
    if not client_id or not client_secret:
        sys.exit(
            "ERROR: WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET must be set.\n"
            "Register a developer app at https://developer.whoop.com\n"
            "Then add to .env:\n"
            "  WHOOP_CLIENT_ID=your-id\n"
            "  WHOOP_CLIENT_SECRET=your-secret"
        )
    return client_id, client_secret


def _exchange_code(code: str, client_id: str, client_secret: str) -> dict:
    """Exchange authorization code for access + refresh tokens."""
    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )
    response.raise_for_status()
    token_data = response.json()
    if "access_token" not in token_data:
        sys.exit(f"ERROR: Token exchange failed. Response: {token_data}")
    return token_data


def start_server() -> None:
    """Run the full OAuth flow: start callback server, open browser, exchange code."""
    client_id, client_secret = _get_client_credentials()

    # Build authorization URL
    auth_params = urlencode({
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
    })
    auth_url = f"{AUTH_URL}?{auth_params}"

    # Check if port is available
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", REDIRECT_PORT))
        except OSError:
            sys.exit(f"ERROR: Port {REDIRECT_PORT} is already in use. "
                     "Close the conflicting process and try again.")

    # Start callback server
    server = HTTPServer(("localhost", REDIRECT_PORT), OAuthCallbackHandler)
    print(f"Opening browser for Whoop authorization...")
    print(f"If browser doesn't open, navigate to:\n{auth_url}\n")

    webbrowser.open(auth_url)

    # Wait for the callback (one request)
    server.handle_request()
    server.server_close()

    if not OAuthCallbackHandler.auth_code:
        sys.exit("ERROR: Did not receive authorization code from Whoop.")

    # Exchange code for tokens
    print("Exchanging authorization code for tokens...")
    token_data = _exchange_code(
        OAuthCallbackHandler.auth_code, client_id, client_secret
    )

    # Calculate expiry time
    import time
    expires_at = time.time() + token_data.get("expires_in", 3600)

    # Store tokens
    save_tokens(
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        expires_at=expires_at,
    )
    print("Tokens stored successfully. You can now run `whoop_sync.py pull`.")


if __name__ == "__main__":
    start_server()