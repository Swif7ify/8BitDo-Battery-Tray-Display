@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title 8BitDo Battery Tray Setup

set "VENV_PY=.venv\Scripts\python.exe"
set "VENV_PYW=.venv\Scripts\pythonw.exe"

if not exist "%VENV_PY%" (
    echo [8BitDo Battery Tray] First-time setup...
    echo.

    set "PYTHON_CMD="
    set "PYTHON_ARG="

    where py >nul 2>&1
    if not errorlevel 1 (
        for %%V in (3.13 3.12 3.11) do (
            if not defined PYTHON_CMD (
                py -%%V -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
                if !errorlevel! equ 0 (
                    set "PYTHON_CMD=py"
                    set "PYTHON_ARG=-%%V"
                )
            )
        )
    )

    if not defined PYTHON_CMD (
        where python >nul 2>&1
        if not errorlevel 1 (
            python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
            if !errorlevel! equ 0 set "PYTHON_CMD=python"
        )
    )

    if not defined PYTHON_CMD (
        echo ERROR: Python 3.11 or newer was not found.
        echo Install 64-bit Python 3.11+ and enable "Add Python to PATH", then run this file again.
        echo.
        pause
        exit /b 1
    )

    echo Creating isolated Python environment...
    "%PYTHON_CMD%" !PYTHON_ARG! -m venv ".venv"
    if errorlevel 1 goto :setup_error
)

"%VENV_PY%" -c "import eightbitdo_battery_tray, pystray, PIL; from winrt.windows.gaming.input import RawGameController" >nul 2>&1
if errorlevel 1 (
    echo Installing/updating required packages...
    "%VENV_PY%" -m pip install --disable-pip-version-check -e .
    if errorlevel 1 goto :setup_error
)

if not exist "%VENV_PYW%" (
    echo ERROR: pythonw.exe is missing from the virtual environment.
    goto :setup_error
)

echo Starting 8BitDo Battery Tray...
start "" "%VENV_PYW%" -m eightbitdo_battery_tray
exit /b 0

:setup_error
echo.
echo ERROR: 8BitDo Battery Tray could not be started.
echo The error above has been left visible so it can be diagnosed.
echo.
pause
exit /b 1
