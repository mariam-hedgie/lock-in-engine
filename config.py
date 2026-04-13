from __future__ import annotations
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent
LOG_DIR  = ROOT_DIR / "logs"

# ── Session plan ─────────────────────────────────────────────────────────────
SESSION_PLAN   = [5, 10, 15, 30, 30, 30, 30, 30]   # minutes per block
TOTAL_MINUTES  = 180

# ── Window ───────────────────────────────────────────────────────────────────
CORNER          = "bottom-right"   # "bottom-right" | "bottom-left" | "top-right" | "top-left"
CORNER_MARGIN   = 20               # px from screen edge
MINI_W, MINI_H  = 280, 88          # collapsed size
FULL_W, FULL_H  = 440, 580         # expanded size
NOTE_H          = 640              # expanded + note field

# ── Focus watcher ─────────────────────────────────────────────────────────────
FOCUS_POLL_SECS    = 2     # how often to check active app
FOCUS_DRIFT_GRACE  = 5     # seconds before a switch counts as drift

# ── Chrome extension URL receiver ────────────────────────────────────────────
# The Chrome extension POSTs the active tab domain to this local port.
# Change if 27182 is already taken on your machine.
URL_SERVER_PORT = 27182

# Domains that count as "on task" — won't be logged as drift.
# Add your study tools so switching to Canvas etc. doesn't get flagged.
ALLOWED_DOMAINS = {
    "canvas.instructure.com",
    "chat.openai.com",
    "claude.ai",
    "www.google.com",
    "google.com",
    "scholar.google.com",
    "pubmed.ncbi.nlm.nih.gov",
    "ncbi.nlm.nih.gov",
    "localhost",
    "127.0.0.1",
}

# ── Git ───────────────────────────────────────────────────────────────────────
GIT_AUTO_COMMIT    = True          # commit logs/ after each session
GIT_AUTO_PUSH      = False         # never push automatically

# ── Themes ────────────────────────────────────────────────────────────────────
THEMES = [
    {"name": "Matcha Night", "bg": "#0f1410", "surface": "#1d2820",
     "accent": "#6fcf8a", "muted": "#7a9480", "text": "#e8f0e9", "danger": "#e07060"},
    {"name": "Blue Hour",    "bg": "#0d1218", "surface": "#1b2433",
     "accent": "#7bb8ff", "muted": "#7a90a8", "text": "#eef4ff", "danger": "#e07060"},
    {"name": "Rose Dust",    "bg": "#150f12", "surface": "#281e24",
     "accent": "#e8829e", "muted": "#9a7a84", "text": "#f9eef4", "danger": "#e07060"},
    {"name": "Plum Ink",     "bg": "#100c18", "surface": "#221d38",
     "accent": "#b49fff", "muted": "#8a80a8", "text": "#f4efff", "danger": "#e07060"},
    {"name": "Sea Glass",    "bg": "#0c1618", "surface": "#1c2c31",
     "accent": "#72d3c9", "muted": "#769aa0", "text": "#ebf7f7", "danger": "#e07060"},
    {"name": "Amber Fog",    "bg": "#171008", "surface": "#2e220f",
     "accent": "#f0b866", "muted": "#a09060", "text": "#fbf3e8", "danger": "#e07060"},
    {"name": "Cocoa Mint",   "bg": "#12100a", "surface": "#28251a",
     "accent": "#a0d4a8", "muted": "#8a9c84", "text": "#f7f4ea", "danger": "#e07060"},
]

# ── Motivational messages (shown every minute) ────────────────────────────────
MESSAGES = [
    "Stay with it.",
    "You're already in motion.",
    "Don't break now.",
    "Eyes on the page.",
    "Keep going.",
]
