@echo off
setlocal
cd /d "%~dp0"

echo.
echo ======================================
echo    Lock-In Engine Setup for Windows
echo ======================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo Install it from https://www.python.org/downloads/windows/
  exit /b 1
)

python --version

python -c "import tkinter" >nul 2>nul
if errorlevel 1 (
  echo.
  echo tkinter is missing.
  echo Reinstall Python and make sure Tcl/Tk support is included.
  exit /b 1
)

if not exist logs mkdir logs
echo Logs folder is ready.

if not exist .git (
  git init >nul 2>nul
  git add . >nul 2>nul
  git commit -m "init: lock-in engine setup" >nul 2>nul
  echo Git repo initialized.
) else (
  echo Git repo already exists.
)

echo.
echo Setup complete.
echo Double-click run.bat or run: python lock_in.py
echo.
