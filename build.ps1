$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Stop any running instances so the binary is not locked during build
Get-Process -Name "8BitDoBatteryTray" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500

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

$iconPath = "$PSScriptRoot\src\eightbitdo_battery_tray\assets\logo.ico"
if (-not (Test-Path $iconPath) -and (Test-Path "$PSScriptRoot\logo.ico")) {
    $iconPath = "$PSScriptRoot\logo.ico"
}

$versionFile = "$PSScriptRoot\file_version_info.txt"

& .\.venv\Scripts\pyinstaller.exe `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "8BitDoBatteryTray" `
    --icon "$iconPath" `
    --version-file "$versionFile" `
    --paths "$PSScriptRoot\src" `
    --add-data "$PSScriptRoot\src\eightbitdo_battery_tray\assets;eightbitdo_battery_tray/assets" `
    --collect-submodules "winrt.windows.gaming.input" `
    --collect-submodules "winrt.windows.devices.power" `
    --collect-submodules "winrt.windows.foundation" `
    --collect-submodules "winrt.windows.foundation.collections" `
    --collect-submodules "winrt.windows.system.power" `
    "$PSScriptRoot\tray_launcher.py"

$exePath = "$PSScriptRoot\dist\8BitDoBatteryTray.exe"
if (-not (Test-Path $exePath)) {
    throw "Build failed: $exePath was not found."
}

# -------------------------------------------------------------
# Authenticode Code Signing
# -------------------------------------------------------------
Write-Host "Configuring Authenticode signature for $exePath..."

if ($env:CODESIGN_PFX -and (Test-Path $env:CODESIGN_PFX)) {
    # Production / Release PFX signing
    $signtool = Get-ChildItem "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe" -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1

    if ($signtool) {
        Write-Host "Signing with SignTool using $env:CODESIGN_PFX..."
        & $signtool.FullName sign `
            /fd SHA256 `
            /f $env:CODESIGN_PFX `
            /p $env:CODESIGN_PASSWORD `
            /tr "http://timestamp.digicert.com" `
            /td SHA256 `
            /d "8BitDo Battery Tray" `
            $exePath
        if ($LASTEXITCODE -ne 0) { throw "Code signing with SignTool failed." }

        Write-Host "Verifying signature with SignTool..."
        & $signtool.FullName verify /pa /v $exePath
    } else {
        Write-Host "Signing with Set-AuthenticodeSignature using $env:CODESIGN_PFX..."
        $pfxCert = Get-PfxCertificate -FilePath $env:CODESIGN_PFX
        Set-AuthenticodeSignature `
            -FilePath $exePath `
            -Certificate $pfxCert `
            -HashAlgorithm SHA256 `
            -TimestampServer "http://timestamp.digicert.com" | Out-Null
    }
} else {
    # Local Developer signing with OneDevPH certificate
    Write-Host "Signing with OneDevPH developer certificate..."
    $cert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
        Where-Object { $_.Subject -like "*OneDevPH*" } |
        Select-Object -First 1

    if (-not $cert) {
        Write-Host "Creating OneDevPH developer code signing certificate..."
        $cert = New-SelfSignedCertificate `
            -Type CodeSigningCert `
            -Subject "CN=OneDevPH, O=OneDevPH" `
            -CertStoreLocation "Cert:\CurrentUser\My" `
            -NotAfter (Get-Date).AddYears(5)
    }

    Set-AuthenticodeSignature `
        -FilePath $exePath `
        -Certificate $cert `
        -HashAlgorithm SHA256 `
        -TimestampServer "http://timestamp.digicert.com" | Out-Null
}

$sig = Get-AuthenticodeSignature $exePath
Write-Host ""
Write-Host "=========================================================="
Write-Host " Build & Signing Complete!"
Write-Host " Executable:  $exePath"
Write-Host " Signer:      $($sig.SignerCertificate.Subject)"
Write-Host " Timestamp:   $($sig.TimeStamperCertificate.Subject)"
Write-Host " Status:      $($sig.Status)"
Write-Host "=========================================================="
