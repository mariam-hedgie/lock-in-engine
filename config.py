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
MINI_W, MINI_H  = 332, 118         # collapsed size
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
     "accent": "#9AF0AE", "muted": "#B7C5BA", "text": "#FAFFFB", "danger": "#FF6D5C"},
    {"name": "Blue Hour",    "bg": "#0d1218", "surface": "#1b2433",
     "accent": "#9FD2FF", "muted": "#B7C3D5", "text": "#FBFDFF", "danger": "#FF6D5C"},
    {"name": "Rose Dust",    "bg": "#150f12", "surface": "#281e24",
     "accent": "#FFAAC2", "muted": "#CBB3BA", "text": "#FFF9FC", "danger": "#FF6D5C"},
    {"name": "Plum Ink",     "bg": "#100c18", "surface": "#221d38",
     "accent": "#D6C7FF", "muted": "#BBB3D6", "text": "#FDFCFF", "danger": "#FF6D5C"},
    {"name": "Sea Glass",    "bg": "#0c1618", "surface": "#1c2c31",
     "accent": "#98F0E7", "muted": "#B1C5C9", "text": "#FAFEFE", "danger": "#FF6D5C"},
    {"name": "Amber Fog",    "bg": "#171008", "surface": "#2e220f",
     "accent": "#FFD898", "muted": "#CCBE9B", "text": "#FFFDF7", "danger": "#FF6D5C"},
    {"name": "Cocoa Mint",   "bg": "#12100a", "surface": "#28251a",
     "accent": "#C7F2CD", "muted": "#BEC4B2", "text": "#FFFDF8", "danger": "#FF6D5C"},
]

# ── Motivational messages (shown every minute) ────────────────────────────────
MESSAGES = [
    "Stay with it.",
    "You're already in motion.",
    "Don't break now.",
    "Eyes on the page.",
    "Keep going.",
]
