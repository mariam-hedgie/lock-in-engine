#!/usr/bin/env bash
# Lock-In Engine launcher
# Double-click this file in Finder to start the app.
# macOS will open a Terminal window and launch the timer.

# Move to the folder this script lives in
cd "$(dirname "$0")"

# Run the app
python3 lock_in.py

# Keep terminal open if there's an error so you can read it
if [ $? -ne 0 ]; then
  echo ""
  echo "Something went wrong. See the error above."
  echo "Press any key to close."
  read -n 1
fi
