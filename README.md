# Lock-In Engine

# PERSONAL TODO
- change this to the most recent repo functionality
- include safari browser


A small desktop focus tool with a floating study timer, short lock-in prompts, session logs, and anti-drift check-ins.

This repo uses Python and `tkinter`, with no third-party Python packages.

## Project Layout

```text
lock-in-engine/
├── lock_in.py
├── focus_watcher.py
├── logger.py
├── config.py
├── setup.sh
├── run.command
└── logs/
```

## Requirements

- Python 3.9 or newer
- `tkinter`
- A terminal you can run Python from

To verify your Python install:

```bash
python3 --version
```

To verify `tkinter` works:

```bash
python3 -m tkinter
```

If that opens a small test window, `tkinter` is available.

## Quick Start

From the project folder:

```bash
python3 lock_in.py
```

Logs are written to `logs/`.

## macOS Setup

### 1. Install Python

Use one of these:

- `python.org` installer
- Homebrew
- an existing Python 3 install

If you use Homebrew and `tkinter` is missing:

```bash
brew install python-tk
```

### 2. Verify `tkinter`

```bash
python3 -m tkinter
```

### 3. Run the app

```bash
python3 lock_in.py
```

You can also try:

```bash
bash setup.sh
```

and then double-click `run.command` from Finder if you want a launcher.

### 4. macOS permissions

The focus watcher may use AppleScript-based app detection depending on how this repo is configured. If macOS asks for permission, allow:

- `Terminal` or your Python app
- `System Events` / Automation access

Path:

- `System Settings`
- `Privacy & Security`
- `Automation`

## Windows Setup

### 1. Install Python

Install Python 3 from:

- the official Python installer
- Microsoft Store Python

During install, make sure `Add Python to PATH` is enabled if you use the python.org installer.

### 2. Verify `tkinter`

In PowerShell or Command Prompt:

```powershell
py -m tkinter
```

If that fails, try:

```powershell
python -m tkinter
```

### 3. Run the app

From the project folder:

```powershell
py lock_in.py
```

If `py` is not available:

```powershell
python lock_in.py
```

### 4. Notes for Windows

- `run.command` is macOS-only
- `setup.sh` is shell-oriented and not the main Windows path
- topmost window behavior should still work through `tkinter`
- app/focus detection may behave differently from macOS depending on the watcher implementation

## Linux Setup

### 1. Install Python and `tkinter`

On Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3 python3-tk
```

On Fedora:

```bash
sudo dnf install python3 python3-tkinter
```

On Arch:

```bash
sudo pacman -S python tk
```

### 2. Verify `tkinter`

```bash
python3 -m tkinter
```

### 3. Run the app

```bash
python3 lock_in.py
```

### 4. Notes for Linux

- window manager behavior can vary
- always-on-top behavior depends partly on your desktop environment
- focus detection may need small adjustments if your desktop session blocks the current watcher approach

## Usage

When you launch the app:

1. Set your run title.
2. Set your allowed study tools.
3. Start the session.
4. Use the anti-drift controls during study:
   - `Allowed Tools`
   - `Open Intention`
   - `Capture`
   - `Return Mode`
   - `Break Glass`

Logs are saved automatically.

## Files Created

Each run can create:

- a text session log in `logs/`
- a CSV capture file in `logs/`

The CSV is useful if you want to review distractions later in Excel.

## Platform Notes

### Supported best on macOS

This project appears to be designed primarily around macOS behavior, especially for focus/app watching and the helper scripts in the repo.

### Windows and Linux

The main `tkinter` app should still run, but you may see small differences in:

- focus watcher behavior
- always-on-top behavior
- notification behavior
- window styling

## Troubleshooting

### `ModuleNotFoundError` or Python command not found

Make sure Python 3 is installed and available on your PATH.

### `No module named tkinter`

Install the platform `tkinter` package:

- macOS Homebrew: `brew install python-tk`
- Ubuntu/Debian: `sudo apt install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`
- Arch: `sudo pacman -S tk`

### The app opens but looks different on my OS

That is expected. `tkinter` rendering varies by platform and theme.

### Focus/app detection does not seem accurate

Start by checking `focus_watcher.py`. That part is the most platform-sensitive piece of the project.

## Development

If you want to tweak the experience, start with:

- `config.py` for plan/theme/settings
- `lock_in.py` for the UI and app flow
- `focus_watcher.py` for app-switch detection
- `logger.py` for session and CSV logging
