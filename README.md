# 8BitDo Ultimate 2 Battery Tray

Minimal Windows tray monitor for the **8BitDo Ultimate 2 Wireless** controller over the 2.4 GHz receiver.

## Safety / performance design

- Uses `Windows.Gaming.Input.RawGameController` only.
- **No HID writes**, feature-report probing, rumble commands, firmware access, controller mode switching, or configuration changes.
- Targets only 8BitDo VID `0x2DC8`, PID `0x310B` (2.4G XInput) and `0x6012` (2.4G DInput).
- Polls once every **10 seconds**. There is no busy loop.
- Runs the battery query on one daemon worker thread so the tray UI stays responsive.
- Uses a Windows named mutex so only one tray instance runs per login session.
- No admin rights, network calls, analytics, telemetry, or cloud services.
- Local logs are capped at 256 KB with two backups under `%LOCALAPPDATA%\8BitDoBatteryTray`.

## Important limitation

Windows can only show a numeric percentage if the controller/driver exposes both remaining and full battery capacity through Windows Gaming Input. If the Ultimate 2's current 2.4G firmware/driver exposes only a coarse level or no capacity, this app intentionally shows `--` rather than guessing a percentage.

This is deliberate: guessing a byte from raw controller packets can display a plausible but false battery percentage and would require lower-level device interaction.

## Install / run

Use 64-bit Python 3.11+ on Windows 10/11.

### Easiest

Double-click:

```text
run.bat
```

It creates a `.venv`, installs the required packages, and starts the tray app.

### Verify battery reporting first

After the environment has been created:

```text
diagnose.bat
```

Expected when Windows exposes exact capacity:

```text
Controller: 8BitDo Ultimate 2 Wireless Controller for PC
VID/PID: 0x2DC8/0x310B
Battery: 83%
```

If it says `exact percentage not exposed by Windows`, the tray will safely display `--` in that connection mode.

## Build a no-console EXE

Open PowerShell in this folder:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build.ps1
```

Output:

```text
dist\8BitDoBatteryTray.exe
```

## Tray behavior

- Tray icon shows the numeric level, e.g. `83` (tooltip: `83%`).
- `--` means disconnected or Windows did not expose exact capacity.
- Double-click/right-click **Refresh** requests an immediate read.
- **Exit** stops the worker and closes cleanly.

## Development checks

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\pytest.exe
```
