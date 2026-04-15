@echo off
setlocal
cd /d "%~dp0"

if not exist logs mkdir logs

where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or not on PATH.
  echo Install it from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)

python -c "import tkinter" >nul 2>nul
if errorlevel 1 (
  echo Python is installed, but tkinter is missing.
  echo Reinstall Python and make sure Tcl/Tk support is included.
  pause
  exit /b 1
)

python lock_in.py
if errorlevel 1 (
  echo.
  echo Something went wrong. See the error above.
  pause
)
