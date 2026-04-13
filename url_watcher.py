from __future__ import annotations

"""
url_watcher.py
Runs a tiny local HTTP server on URL_SERVER_PORT.
The Chrome extension POSTs JSON like:
  { "url": "https://www.instagram.com/...", "domain": "www.instagram.com" }
whenever the active tab changes.

The server calls on_drift(domain, secs) / on_return() using the same
interface as FocusWatcher, so lock_in.py treats them identically.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import urlparse

from config import URL_SERVER_PORT, ALLOWED_DOMAINS, FOCUS_DRIFT_GRACE


class URLWatcher:
    """
    Starts a background HTTP server.
    Calls on_drift(domain, seconds) when the user has been on a
    non-allowed domain for more than FOCUS_DRIFT_GRACE seconds.
    Calls on_return() when they come back to an allowed domain.
    """

    def __init__(
        self,
        on_drift: Callable[[str, int], None],
        on_return: Callable[[], None],
    ) -> None:
        self._on_drift  = on_drift
        self._on_return = on_return
        self._active    = False       # only track during countdown blocks
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

        # Drift tracking
        self._away_since: float | None = None
        self._away_domain = ""

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self) -> None:
        watcher = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body   = self.rfile.read(length)
                    data   = json.loads(body)
                    domain = data.get("domain", "") or _domain_from_url(data.get("url", ""))
                    watcher._handle_domain(domain)
                except Exception:
                    pass
                self._respond()

            def do_OPTIONS(self):
                # Chrome extension pre-flight
                self._respond()

            def _respond(self):
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def log_message(self, *args):
                pass  # silence default HTTP logging

        try:
            self._server = HTTPServer(("127.0.0.1", URL_SERVER_PORT), Handler)
            self._thread = threading.Thread(
                target=self._server.serve_forever, daemon=True
            )
            self._thread.start()
        except OSError:
            # Port already in use — silently skip (focus_watcher still works)
            pass

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()

    def set_active(self, active: bool) -> None:
        self._active = active
        if not active:
            self._away_since  = None
            self._away_domain = ""

    # ── Internal ─────────────────────────────────────────────────────────────

    def _handle_domain(self, domain: str) -> None:
        if not domain:
            return
        is_allowed = _is_allowed(domain)

        if is_allowed:
            if self._away_since is not None and self._active:
                secs = int(time.time() - self._away_since)
                if secs >= FOCUS_DRIFT_GRACE:
                    self._on_drift(self._away_domain, secs)
                self._away_since  = None
                self._away_domain = ""
                self._on_return()
        else:
            if self._active and self._away_since is None:
                self._away_since  = time.time()
                self._away_domain = domain


# ── Helpers ───────────────────────────────────────────────────────────────────

def _domain_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


def _is_allowed(domain: str) -> bool:
    domain = domain.lower().lstrip("www.")
    for allowed in ALLOWED_DOMAINS:
        clean = allowed.lower().lstrip("www.")
        if domain == clean or domain.endswith("." + clean):
            return True
    return False
