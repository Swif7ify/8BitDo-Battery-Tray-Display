# 8BitDo Ultimate 2 Battery Tray

A lightweight, secure, and read-only Windows system tray monitor for the **8BitDo Ultimate 2 Wireless** controller (2.4 GHz wireless receiver & Bluetooth/DInput modes).

---

## Features

- **Live System Tray Level**: Real-time numeric battery display right in your Windows taskbar.
- **Smart Status Color Coding**:
  - 🟢 **Green outline**: Controller is actively charging (docked or plugged in via USB-C).
  - ⚪ **Crisp light gray outline**: Normal operating battery level ($> 25\%$).
  - 🟠 **Amber outline**: Low battery warning ($\le 25\%$).
  - 🔴 **Red outline**: Critical battery alert ($\le 15\%$).
  - ⚪ **`--` indicator**: Controller disconnected, asleep, or capacity metrics not exposed by driver.
- **Per-Monitor V2 DPI Aware**: Crystal-clear, sharp text rendering on 100%, 125%, 150%, and 200%+ display scalings.
- **100% Read-Only & Safe**: Zero HID writes, zero feature reports, zero rumble commands, and zero firmware modifications.
- **Ultra-Low Resource Footprint**: Memory-cached icons and fonts, background daemon polling every 10 seconds, zero busy-waiting.
- **Single-Instance Session Mutex**: Prevents duplicate tray instances per Windows user session.
- **Complete Privacy**: 0% telemetry, 0% analytics, 0% network connectivity. Local logs are strictly capped at 256 KB.

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                    Windows User Session                      │
│                                                              │
│  ┌─────────────────────────┐      ┌───────────────────────┐  │
│  │   8BitDo Battery Tray   │      │  SingleInstance Guard │  │
│  │    (TrayApplication)    │◄────►│  (Local Named Mutex)  │  │
│  └───────────┬─────────────┘      └───────────────────────┘  │
│              │                                               │
│              ▼ (Event-driven polling every 10s)              │
│  ┌─────────────────────────┐                                 │
│  │     BatteryMonitor      │                                 │
│  │     (Worker Thread)     │                                 │
│  └───────────┬─────────────┘                                 │
│              │                                               │
│              ▼                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Windows Gaming Input (WGI) Provider (Read-Only)        │  │
│  │ - RawGameController.raw_game_controllers               │  │
│  │ - Matches VID 0x2DC8, PID 0x310B (2.4G) / 0x6012 (BT) │  │
│  │ - controller.try_get_battery_report()                  │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

1. **Enumeration**: Queries Windows Gaming Input (`Windows.Gaming.Input.RawGameController`) for 8BitDo controllers (Vendor ID `0x2DC8`, Product IDs `0x310B` for 2.4G XInput and `0x6012` for Bluetooth/DInput).
2. **Telemetry Extraction**: Fetches `BatteryReport` for remaining and full milliwatt-hours capacity and charging status (`BatteryStatus.Charging` / `charge_rate_in_milliwatts > 0`).
3. **Dynamic Tray Rendering**: Dynamically paints a high-contrast 64x64 rounded badge with font bearing alignment and updates the notification icon and tooltip.

---

## Quick Start

### Prerequisites
- **Operating System**: Windows 10 or Windows 11 (64-bit).
- **Python**: Python 3.11, 3.12, 3.13, or newer.

---

### Option 1: Run via Batch Script (Easiest)

Simply double-click:
```bat
run.bat
```
- Automatically checks for Python 3.11+.
- Creates an isolated `.venv` virtual environment on first launch.
- Installs all dependencies automatically.
- Launches the tray app silently in the background (`pythonw.exe`).

---

### Option 2: Pre-check Controller with Diagnostics

To inspect what Windows is reporting before launching the tray app:
```bat
diagnose.bat
```
*Or via command line:*
```powershell
.\.venv\Scripts\python.exe -m eightbitdo_battery_tray --once
```

**Expected output when controller is connected:**
```text
Controller: 8BitDo Ultimate 2 Wireless Controller for PC
VID/PID: 0x2DC8/0x310B
Battery: 85%
Detail: Battery percentage supplied by Windows Gaming Input.
```

**Output when controller is charging:**
```text
Controller: 8BitDo Ultimate 2 Wireless Controller for PC
VID/PID: 0x2DC8/0x310B
Battery: 85% (Charging)
Detail: Battery percentage supplied by Windows Gaming Input.
```

**Output when controller is disconnected:**
```text
Controller: not detected
Detail: 8BitDo Ultimate 2 not detected in 2.4 GHz XInput/DInput mode.
```

---

### Option 3: Build a Standalone `.exe` (No Python Needed)

To package a single-file executable that runs without Python installed:

1. Open PowerShell in this folder.
2. Run:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\build.ps1
   ```
3. Your standalone executable will be created at:
   ```text
   dist\8BitDoBatteryTray.exe
   ```

You can move `dist\8BitDoBatteryTray.exe` anywhere you like.

---

## Run on Windows Startup

To have the monitor launch automatically when you sign in:

1. Press `Win + R`, type `shell:startup`, and press **Enter**.
2. Right-click inside the folder $\rightarrow$ **New** $\rightarrow$ **Shortcut**.
3. Set the target to either:
   - Your built `dist\8BitDoBatteryTray.exe`, or
   - `run.bat` in this repository.
4. Click **Next** and **Finish**.

---

## Tray Controls & Context Menu

Right-click the icon in your system tray to access the menu:

| Menu Action | Description |
| :--- | :--- |
| **8BitDo Battery Tray — Running** | Header indicating the application is active. |
| **Refresh now** *(Default / Double-Click)* | Triggers an immediate controller battery poll. |
| **Open log** | Opens `%LOCALAPPDATA%\8BitDoBatteryTray\app.log` in your default text editor. |
| **Exit** | Cleanly terminates the background polling worker and exits the application. |

---

## Security, Safety & Privacy

- **Zero Device Modification**: Operates strictly through high-level WinRT interfaces. Does not open raw HID handles, send calibration/configuration packets, toggle controller modes, or write outputs.
- **Least Privilege**: Does not require Administrator privileges.
- **Session-Scoped Mutex**: Uses a `Local\` Windows named mutex (`Local\EightBitDoUltimate2BatteryTray_v1`) to prevent multiple tray icons in the same user session without crossing session boundaries.
- **Log Sanitation**: Local rotating logs never exceed 256 KB (with a maximum of 2 backup rotations). No personal data or credentials are ever recorded.
- **Offline Assurance**: Contains no network sockets, HTTP requests, or external telemetry hooks.

---

## Development & Testing

### Install Dependencies
```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Code Style & Linter
Check with Ruff (strictly configured to 0 errors):
```powershell
.\.venv\Scripts\ruff.exe check src tests
```

### Automated Unit Tests
Run the pytest test suite:
```powershell
.\.venv\Scripts\pytest.exe -v
```

All 14 automated tests cover:
- Unit percentage calculations and boundary clampings.
- Immutability of `BatterySnapshot`.
- Controller VID/PID matching and disconnection fault tolerance.
- Battery charging state detection (`charge_rate` and `status`).
- Icon generation, sizing, glyph bearing centering, and outline colors.
- Named mutex acquisition, duplicate conflict detection, and cleanup.
- Worker thread lifecycle and refresh signalling.

---

## License

This project is licensed under the MIT License.
