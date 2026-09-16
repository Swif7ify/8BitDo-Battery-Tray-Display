@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo The virtual environment does not exist yet.
  echo Run run.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m eightbitdo_battery_tray --once
echo.
pause
