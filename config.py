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
MINI_W, MINI_H  = 312, 100         # collapsed size
FULL_W, FULL_H  = 500, 680         # expanded size
NOTE_H          = 740              # expanded + note field

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
     "accent": "#8BE5A1", "muted": "#A8B7AB", "text": "#F4FAF5", "danger": "#FF8A78"},
    {"name": "Blue Hour",    "bg": "#0d1218", "surface": "#1b2433",
     "accent": "#94CBFF", "muted": "#A8B6C8", "text": "#F5F9FF", "danger": "#FF8A78"},
    {"name": "Rose Dust",    "bg": "#150f12", "surface": "#281e24",
     "accent": "#F39BB4", "muted": "#C0A6AE", "text": "#FFF7FB", "danger": "#FF8A78"},
    {"name": "Plum Ink",     "bg": "#100c18", "surface": "#221d38",
     "accent": "#C9B7FF", "muted": "#B1A9CD", "text": "#FBF8FF", "danger": "#FF8A78"},
    {"name": "Sea Glass",    "bg": "#0c1618", "surface": "#1c2c31",
     "accent": "#8CE6DD", "muted": "#A2B9BE", "text": "#F3FBFB", "danger": "#FF8A78"},
    {"name": "Amber Fog",    "bg": "#171008", "surface": "#2e220f",
     "accent": "#FFD08A", "muted": "#C4B58E", "text": "#FFF9F0", "danger": "#FF8A78"},
    {"name": "Cocoa Mint",   "bg": "#12100a", "surface": "#28251a",
     "accent": "#B8E9BF", "muted": "#AFB6A3", "text": "#FFFDF5", "danger": "#FF8A78"},
]

# ── Motivational messages (shown every minute) ────────────────────────────────
MESSAGES = [
    "Stay with it.",
    "You're already in motion.",
    "Don't break now.",
    "Eyes on the page.",
    "Keep going.",
]
