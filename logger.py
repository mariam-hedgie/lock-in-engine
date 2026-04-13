from __future__ import annotations

import csv
import subprocess
from datetime import datetime
from pathlib import Path

from config import LOG_DIR, ROOT_DIR, GIT_AUTO_COMMIT, SESSION_PLAN, TOTAL_MINUTES


def _sanitize(title: str) -> str:
    import re
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", title.strip())
    cleaned = cleaned.strip("-._")
    return cleaned or "session"


class SessionLogger:
    def __init__(self, title: str, allowed_tools: list[str]) -> None:
        LOG_DIR.mkdir(exist_ok=True)
        self.title = title
        self.started = datetime.now()
        stamp = self.started.strftime("%Y-%m-%d_%H-%M")
        slug  = _sanitize(title)
        self.log_path     = LOG_DIR / f"{stamp}_{slug}.txt"
        self.capture_path = LOG_DIR / f"{stamp}_{slug}_captures.csv"
        self._init_log(title, allowed_tools)
        self._init_csv()

    # ── Setup ─────────────────────────────────────────────────────────────────
    def _init_log(self, title: str, tools: list[str]) -> None:
        plan_str = " → ".join(f"{m}min" for m in SESSION_PLAN)
        with self.log_path.open("w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n")
            f.write(f"LOCK-IN SESSION\n")
            f.write(f"{'='*60}\n")
            f.write(f"Title      : {title}\n")
            f.write(f"Started    : {self.started.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Plan       : {plan_str}\n")
            f.write(f"Total      : {TOTAL_MINUTES} minutes\n")
            f.write(f"Tools      : {', '.join(tools)}\n")
            f.write(f"{'='*60}\n\n")

    def _init_csv(self) -> None:
        with self.capture_path.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                ["timestamp", "kind", "category", "target", "notes"]
            )

    # ── Writing ───────────────────────────────────────────────────────────────
    def append(self, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] {text}\n")

    def capture(self, kind: str, category: str, target: str, notes: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.capture_path.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([ts, kind, category, target, notes])
        self.append(f"{kind} | {category} | {target} | {notes}")

    def block_complete(self, block_num: int, total_blocks: int,
                       minutes: int, note: str) -> None:
        self.append(
            f"Block {block_num:02d}/{total_blocks} complete | "
            f"{minutes}min | note: {note}"
        )

    def drift(self, app_name: str, duration_secs: int) -> None:
        self.capture("drift", "focus", app_name, f"{duration_secs}s away")

    def finish(self, total_done: int, drift_secs: int,
               capture_count: int) -> None:
        finished = datetime.now()
        elapsed  = finished - self.started
        elapsed_str = str(elapsed).split(".")[0]
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"FINISHED   : {finished.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Elapsed    : {elapsed_str}\n")
            f.write(f"Completed  : {total_done}/{TOTAL_MINUTES} min\n")
            f.write(f"Drift      : ~{drift_secs}s across all blocks\n")
            f.write(f"Distractions captured: {capture_count}\n")
            f.write(f"{'='*60}\n")
        if GIT_AUTO_COMMIT:
            self._git_commit()

    # ── Git ───────────────────────────────────────────────────────────────────
    def _git_commit(self) -> None:
        try:
            stamp = self.started.strftime("%Y-%m-%d %H:%M")
            msg   = f"session: {self.title} — {stamp}"
            subprocess.run(
                ["git", "add", str(LOG_DIR)],
                cwd=ROOT_DIR, check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", msg],
                cwd=ROOT_DIR, check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            pass   # no git repo or nothing to commit — silent
        except FileNotFoundError:
            pass   # git not installed — silent
