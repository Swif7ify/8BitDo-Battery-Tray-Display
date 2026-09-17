$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    $pythonCmd = $null
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($ver in @("-3.14", "-3.13", "-3.12", "-3.11")) {
            & py $ver -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
            if ($LASTEXITCODE -eq 0) {
                $pythonCmd = @("py", $ver)
                break
            }
        }
    }
    if (-not $pythonCmd -and (Get-Command python -ErrorAction SilentlyContinue)) {
        & python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = @("python")
        }
    }
    if (-not $pythonCmd) {
        throw "Python 3.11 or newer is required to build this project."
    }
    & $pythonCmd -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -e ".[dev]"

# Ensure logo.ico exists from logo.png for executable embedding
if (Test-Path "$PSScriptRoot\logo.png") {
    & .\.venv\Scripts\python.exe -c "
from PIL import Image
img = Image.open('logo.png')
img.save('logo.ico', format='ICO', sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
"
    Copy-Item "$PSScriptRoot\logo.png", "$PSScriptRoot\logo.ico" "$PSScriptRoot\src\eightbitdo_battery_tray\assets\" -Force
}

$iconArg = @()
if (Test-Path "$PSScriptRoot\logo.ico") {
    $iconArg = @("--icon", "$PSScriptRoot\logo.ico")
}

& .\.venv\Scripts\pyinstaller.exe `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "8BitDoBatteryTray" `
    @iconArg `
    --paths "$PSScriptRoot\src" `
    --add-data "$PSScriptRoot\src\eightbitdo_battery_tray\assets;eightbitdo_battery_tray/assets" `
    --collect-submodules "winrt.windows.gaming.input" `
    --collect-submodules "winrt.windows.devices.power" `
    --collect-submodules "winrt.windows.foundation" `
    --collect-submodules "winrt.windows.foundation.collections" `
    --collect-submodules "winrt.windows.system.power" `
    "$PSScriptRoot\tray_launcher.py"

Write-Host "Built: $PSScriptRoot\dist\8BitDoBatteryTray.exe"
