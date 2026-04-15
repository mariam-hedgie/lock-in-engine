#!/usr/bin/env bash
# Lock-In Engine launcher
# Double-click this file in Finder to start the app.
# macOS will open a Terminal window and launch the timer.

set -u

# Move to the folder this script lives in
cd "$(dirname "$0")"

mkdir -p logs

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is not installed."
  echo "Install Python from https://www.python.org/downloads/mac-osx/"
  echo "Then try double-clicking this file again."
  echo ""
  echo "Press any key to close."
  read -n 1
  exit 1
fi

if ! python3 -c "import tkinter" >/dev/null 2>&1; then
  echo "Python is installed, but tkinter is missing."
  echo "Install the python.org macOS build, or run: brew install python-tk"
  echo ""
  echo "Press any key to close."
  read -n 1
  exit 1
fi

# Run the app
python3 lock_in.py

# Keep terminal open if there's an error so you can read it
if [ $? -ne 0 ]; then
  echo ""
  echo "Something went wrong. See the error above."
  echo "Press any key to close."
  read -n 1
fi
