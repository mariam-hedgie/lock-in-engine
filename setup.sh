#!/usr/bin/env bash
# Lock-In Engine — one-time setup
# Run once: bash setup.sh

set -e

echo ""
echo "╔══════════════════════════════╗"
echo "║   Lock-In Engine · Setup     ║"
echo "╚══════════════════════════════╝"
echo ""

# ── Python check ─────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "✗ python3 not found."
  echo "  Install it from https://www.python.org/downloads/ or via Homebrew:"
  echo "  brew install python3"
  exit 1
fi

PYTHON=$(command -v python3)
echo "✓ Python: $($PYTHON --version)"

# ── tkinter check (built-in on macOS system Python, sometimes missing) ────────
if ! $PYTHON -c "import tkinter" 2>/dev/null; then
  echo ""
  echo "✗ tkinter not found. Fix options:"
  echo "  • Homebrew Python: brew install python-tk"
  echo "  • Or install from python.org (includes tkinter by default)"
  exit 1
fi
echo "✓ tkinter: available"

# ── Create logs dir ───────────────────────────────────────────────────────────
mkdir -p logs
echo "✓ logs/ directory ready"

# ── Permissions ───────────────────────────────────────────────────────────────
chmod +x run.command
echo "✓ run.command is executable"

# ── Git init (if not already a repo) ─────────────────────────────────────────
if [ ! -d ".git" ]; then
  git init -q
  echo "✓ git repo initialised"
  # Initial commit so future session commits have a parent
  git add .
  git commit -q -m "init: lock-in engine setup"
  echo "✓ initial git commit done"
else
  echo "✓ git repo already exists"
fi

# ── macOS: grant Accessibility permission hint ────────────────────────────────
echo ""
echo "⚠  Focus detection uses System Events (osascript)."
echo "   If you get a permissions prompt, click OK — or go to:"
echo "   System Settings → Privacy & Security → Automation"
echo "   and allow Terminal (or your Python app) to control System Events."
echo ""

echo "╔══════════════════════════════╗"
echo "║   Setup complete!            ║"
echo "║   Double-click run.command   ║"
echo "║   or: python3 lock_in.py     ║"
echo "╚══════════════════════════════╝"
echo ""
