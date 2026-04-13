# Lock-In Engine

A corner overlay focus timer for macOS. Stays on top of everything, tracks when you switch apps, and saves session logs automatically.

## Structure

```
lock-in-engine/
├── lock_in.py          ← main app
├── focus_watcher.py    ← background app-switch detection
├── logger.py           ← session log + CSV capture writer
├── config.py           ← all settings (corner, themes, session plan)
├── setup.sh            ← one-time setup
├── run.command         ← double-click to launch from Finder
└── logs/               ← auto-created, open in VSCode
    ├── 2025-01-15_14-30_mcat-orgo.txt
    └── 2025-01-15_14-30_mcat-orgo_captures.csv
```

## Setup (once)

```bash
bash setup.sh
```

This checks Python + tkinter, creates `logs/`, makes `run.command` executable, and does an initial git commit.

## Running

**From Finder / Desktop:**  
Double-click `run.command`. macOS opens a terminal and launches the app.

**From terminal:**
```bash
python3 lock_in.py
```

**From VSCode:**  
Open the folder, then in the integrated terminal: `python3 lock_in.py`

## Usage

- **Collapsed:** tiny pill in the corner — shows timer and block. Click to expand.
- **Expanded:** full UI with action buttons. Press Escape or click away to collapse.
- **Ctrl+P:** panic mode (3-minute starter block)
- **Ctrl+Q:** quit

### During a block
- **Tools** — update allowed study tools
- **Intention** — log what you're opening and why before you open it
- **Capture** — save a distraction thought and keep moving
- **Return** — check if you're still on task
- **Glass 🔴** — break glass: name it before you leave

## Chrome extension (URL tracking)

The extension reports the active tab's domain to Lock-In Engine so it can log *which website* you're on inside Chrome, not just that Chrome is open.

### Install (one time)

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked**
4. Select the `chrome-extension/` folder inside this repo
5. Done — the extension runs silently in the background

### How it works

- When you switch tabs or navigate, the extension POSTs the domain to `http://127.0.0.1:27182`
- Lock-In Engine's URL server receives it and checks against `ALLOWED_DOMAINS` in `config.py`
- Allowed domains (Canvas, ChatGPT, Google Scholar etc.) are not logged as drift
- Everything else (instagram.com, twitter.com, youtube.com etc.) is logged as a drift event — same format as an app-switch

### Customise allowed domains

Edit `ALLOWED_DOMAINS` in `config.py` to whitelist your study tools:

```python
ALLOWED_DOMAINS = {
    "canvas.instructure.com",
    "chat.openai.com",
    "pubmed.ncbi.nlm.nih.gov",
    # add yours here
}
```

### If the extension can't connect

That just means Lock-In Engine isn't running — the extension silently ignores connection errors. App-switch detection via `osascript` continues to work regardless.



Every session creates two files in `logs/`:

- `YYYY-MM-DD_HH-MM_title.txt` — human-readable session log
- `YYYY-MM-DD_HH-MM_title_captures.csv` — structured capture events

Open `logs/` in VSCode to see all sessions. After each session a `git commit` is made automatically so every session is in your repo history. Push manually when you want.

## Settings

Edit `config.py` to change:
- `CORNER` — which corner the widget lives in (`"bottom-right"` etc.)
- `CORNER_MARGIN` — distance from screen edge
- `MINI_W / MINI_H` — collapsed size
- `SESSION_PLAN` — block durations in minutes
- `GIT_AUTO_COMMIT` — set to `False` to disable auto-commits

## macOS permissions

Focus detection uses `osascript` to check the frontmost app every 2 seconds. On first run macOS may ask for Automation permission:

> System Settings → Privacy & Security → Automation → Terminal → System Events ✓

This is required for app-switch detection to work.

## Requirements

- macOS 12+
- Python 3.9+
- tkinter (included with python.org installer; for Homebrew: `brew install python-tk`)
- No other dependencies
