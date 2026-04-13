from __future__ import annotations

import subprocess
import threading
import time
from typing import Callable

from config import FOCUS_POLL_SECS, FOCUS_DRIFT_GRACE


def _get_active_app() -> str:
    """Return the name of the frontmost macOS application."""
    try:
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to get name of first application process whose frontmost is true'],
            capture_output=True, text=True, timeout=2,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


class FocusWatcher:
    """
    Polls the active macOS app every FOCUS_POLL_SECS seconds.
    Calls on_drift(app_name, seconds) when the user has been away
    for more than FOCUS_DRIFT_GRACE seconds.
    Calls on_return() when they come back.
    """

    def __init__(
        self,
        own_app_names: list[str],
        on_drift: Callable[[str, int], None],
        on_return: Callable[[], None],
    ) -> None:
        # Names that count as "still focused" (the Python process shows up
        # as "Python" or "python3" in System Events)
        self._own = {n.lower() for n in own_app_names}
        self._on_drift  = on_drift
        self._on_return = on_return

        self._running     = False
        self._thread: threading.Thread | None = None
        self._away_since: float | None = None
        self._away_app    = ""
        self._active      = False   # whether watcher is tracking (only during countdown)

    # ── Control ───────────────────────────────────────────────────────────────
    def start(self) -> None:
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def set_active(self, active: bool) -> None:
        """Only log drift during countdown blocks."""
        self._active = active
        if not active:
            self._away_since = None

    # ── Loop ─────────────────────────────────────────────────────────────────
    def _loop(self) -> None:
        while self._running:
            time.sleep(FOCUS_POLL_SECS)
            if not self._active:
                continue
            try:
                app = _get_active_app()
                is_own = app.lower() in self._own or app == "unknown"

                if is_own:
                    if self._away_since is not None:
                        away_secs = int(time.time() - self._away_since)
                        if away_secs >= FOCUS_DRIFT_GRACE:
                            self._on_drift(self._away_app, away_secs)
                        self._away_since = None
                        self._away_app   = ""
                        self._on_return()
                else:
                    if self._away_since is None:
                        self._away_since = time.time()
                        self._away_app   = app
            except Exception:
                pass
