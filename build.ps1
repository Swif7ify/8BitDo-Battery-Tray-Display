$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    py -3.11 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -e ".[dev]"
& .\.venv\Scripts\pyinstaller.exe `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "8BitDoBatteryTray" `
    --paths "$PSScriptRoot\src" `
    --collect-submodules "winrt.windows.gaming.input" `
    --collect-submodules "winrt.windows.devices.power" `
    --collect-submodules "winrt.windows.foundation" `
    "$PSScriptRoot\tray_launcher.py"

Write-Host "Built: $PSScriptRoot\dist\8BitDoBatteryTray.exe"
