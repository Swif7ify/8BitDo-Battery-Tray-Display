# 8BitDo Ultimate 2 Battery Tray

A lightweight, secure, and read-only Windows system tray monitor for the **8BitDo Ultimate 2 Wireless** controller (Bluetooth LE & 2.4 GHz wireless receiver modes).

Featuring a **large, transparent battery tray icon** that displays either the **exact percentage number** (when Bluetooth dual-mode is active) or **vertical capacity blocks** (in 2.4 GHz coarse mode), with zero gameplay interference.

---

## Features

- **Large, Transparent Battery Icon**: Seamlessly floats on your Windows taskbar with no dark background box, featuring high-contrast drop-shadow outlines for crystal-clear visibility on both dark and light Windows themes.
- **Smart Dual-Display Modes**:
  - **Bluetooth Dual-Mode (Exact %)**: When Bluetooth is active, the icon displays the bold numeric percentage (e.g. `88%`) inside the battery, color-coded to the current level:
    - 🟢 **Vivid Green**: High / Healthy battery ($> 70\%$).
    - 🟡 **Warm Gold / Amber**: Medium battery ($31\% - 70\%$).
    - 🟠 **Orange / Red**: Low battery warning ($\le 30\%$).
  - **2.4 GHz Coarse Mode (Segments)**: When operating exclusively over the 2.4 GHz USB dongle, the icon displays 3 bold vertical capacity blocks (Full = 3 bars, Medium = 2 bars, Low = 1 bar).
  - ⚡ **Electric Cyan with Lightning Bolt**: Controller is actively charging (docked or USB-C).
  - ⚪ **Muted Neutral Cross**: Controller is disconnected or in sleep mode.
- **Accurate Dual Connection Support**:
  - **Bluetooth LE Mode**: Reads the exact hardware battery gauge byte (e.g. `88%`) directly from Windows' Bluetooth LE GATT Battery Service via native `cfgmgr32`.
  - **2.4 GHz Dongle Mode**: Automatically falls back to Windows Gaming Input for the 2.4 GHz receiver (`USB\VID_2DC8&PID_310B` / `0x6012`).
- **Informative Tooltips & Context Menu**:
  - Hovering over the tray icon displays exact percentage, charging status, and connection mode (e.g., `8BitDo Ultimate 2 — 88% [Bluetooth LE]`).
  - Right-click menu displays real-time connection status (`● 8BitDo: 88% via Bluetooth LE`), instant manual refresh, diagnostic log viewer, and clean exit.
- **100% Read-Only & Safe**:
  - **Zero HID writes**: No arbitrary feature reports or rumble packets injected into your game stream.
  - Zero dropped inputs, zero input lag, zero controller desync.
- **Per-Monitor V2 DPI Aware**: Sharp, crystal-clear rendering across all taskbar scaling factors (100%, 125%, 150%, 200%+).
- **Single-Instance Session Mutex**: Prevents duplicate tray instances per Windows user session.
- **Complete Privacy**: 0% telemetry, 0% analytics, 0% network connectivity. Local logs are strictly capped at 256 KB.

---

## How It Works

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Windows User Session                           │
│                                                                        │
│  ┌─────────────────────────────┐      ┌─────────────────────────────┐  │
│  │     8BitDo Battery Tray     │      │    SingleInstance Guard     │  │
│  │      (TrayApplication)      │◄────►│    (Local Named Mutex)      │  │
│  └──────────────┬──────────────┘      └─────────────────────────────┘  │
│                 │                                                      │
│                 ▼ (Polled every 10s via worker thread)                 │
│  ┌─────────────────────────────┐                                       │
│  │   CompositeBatteryProvider  │                                       │
│  └──────────────┬──────────────┘                                       │
│                 │                                                      │
│        ┌────────┴────────────────────────────────────────┐             │
│        ▼                                                 ▼             │
│  ┌───────────────────────────┐             ┌─────────────────────────┐ │
│  │ WindowsBluetoothProvider  │             │ WindowsGamingInput (WGI)│ │
│  │ - SetupAPI / cfgmgr32     │             │ - RawGameController     │ │
│  │ - PKEY_BatteryPercentage  │             │ - 2.4 GHz USB Receiver  │ │
│  │ - Accurate hardware gauge │             │ - XInput / DInput tiers │ │
│  │   (e.g., exact 88%)       │             │   (Full/Med/Low/Empty)  │ │
│  └───────────────────────────┘             └─────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

### Why the Color Checker? (Bluetooth vs. 2.4 GHz)

- **Bluetooth LE**: Windows natively queries the standard Bluetooth Battery Service (GATT `0x180F`) and stores the exact battery byte in the device property cache (`PKEY_Device_BatteryPercentage`). When connected via Bluetooth, the app reads this exact percentage (e.g. `88%`).
- **2.4 GHz USB Receiver**: When connected to the 2.4 GHz wireless adapter, the receiver presents to Windows as a standard Microsoft XInput controller (`Xbox 360 Controller for Windows`). Microsoft's XInput protocol only transmits 4 coarse 2-bit battery states (`Full`, `Medium`, `Low`, `Critical`). Windows translates `Full` to synthetic $100\%$ capacity.
- **Our Approach**: Rather than displaying misleading coarse numbers in 2.4 GHz mode, the system tray icon uses an intuitive **color-coded 4-segment battery checker**. The exact percentage is always visible when you hover over the tray icon or right-click the menu.

---

### 💡 The "Dual-Radio" Setup: Battery Life & Latency Impact

Many users pair their 8BitDo controller over Bluetooth once, and then use the **2.4 GHz USB wireless receiver** for daily PC gaming. This unlocks a unique "dual-radio" synergy:

```
┌─────────────────────────┐
│   8BitDo Ultimate 2     │
│   Wireless Controller   │
└────────────┬────────────┘
             │
             ├───► [2.4 GHz RF] ────────► 2.4G USB Dongle ──► Game Inputs (Zero Lag)
             │
             └───► [Bluetooth LE] ─────► Windows BT Stack ──► Battery Telemetry (Exact 88%)
```

#### Frequently Asked Questions:

1. **Does this drain the controller's battery faster?**
   - **Virtually zero impact ($< 1\%$)**: The controller uses **Bluetooth Low Energy (BLE)** GATT telemetry, not high-bandwidth classic Bluetooth audio or gameplay streaming.
   - BLE telemetry draws mere microamps ($\sim 0.05\text{ mA}$) with periodic heartbeat intervals.
   - By comparison, the controller's active 2.4 GHz RF radio, Hall-effect joysticks, internal MCU, and dual rumble motors draw $\sim 30\text{ mA} - 75\text{ mA}$. The BLE beacon is completely negligible.

2. **Does it cause any game input lag or latency?**
   - **Zero input lag**: All game inputs (buttons, triggers, analog sticks) travel exclusively through the dedicated 2.4 GHz USB adapter. Bluetooth is used solely for passive battery queries.

3. **Does it consume laptop/PC battery?**
   - **No**: Windows handles Bluetooth LE device property updates in low-power idle states via hardware interrupts on your Wi-Fi/BT chip.

4. **Can I turn off Bluetooth on my laptop?**
   - **Yes, completely optional**:
     - **Bluetooth ON**: You get high-speed 2.4 GHz gaming **plus** exact 1% battery percentage reporting (e.g. `88%`).
     - **Bluetooth OFF**: The app seamlessly switches to 2.4 GHz mode, showing the **4-segment color checker** (e.g. 4 Vivid Green bars for High/Full).

---

## Quick Start

### 🚀 Download Pre-Built Executable (Recommended)

If you just want to run the app without installing Python or cloning source code:
1. Navigate to the **[GitHub Releases](https://github.com/Swif7ify/8BitDo-Battery-Tray-Display/releases)** page.
2. Under **Assets**, download the standalone binary:
   ```
   8BitDoBatteryTray.exe
   ```
3. Double-click the downloaded `.exe` to run! It immediately minimizes to your Windows system tray.

---

### Prerequisites (For Running or Building from Source)
- **Operating System**: Windows 10 or Windows 11 (64-bit).
- **Python**: Python 3.11, 3.12, 3.13, or newer (only required if running from source).

---

### Option 1: Run via Batch Script (From Source)

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

**Expected output when connected via Bluetooth:**
```text
Controller: 8BitDo Ultimate 2 Wireless [Bluetooth LE]
Battery: 88%
Detail: Battery percentage supplied by Bluetooth LE (accurate hardware gauge).
```

**Expected output when connected via 2.4 GHz Wireless Receiver:**
```text
Controller: 8BitDo Ultimate 2 Wireless [2.4GHz Wireless]
VID/PID: 0x2DC8/0x310B
Battery: 100%
Detail: Battery level supplied by Windows Gaming Input (2.4 GHz receiver).
```

**Output when controller is charging:**
```text
Controller: 8BitDo Ultimate 2 Wireless [2.4GHz Wireless]
VID/PID: 0x2DC8/0x310B
Battery: 100% (Charging)
Detail: Battery level supplied by Windows Gaming Input (2.4 GHz receiver).
```

**Output when controller is disconnected:**
```text
Controller: not detected
Detail: 8BitDo controller not detected via Bluetooth or 2.4 GHz wireless.
```

---

### Option 3: Compile Standalone `.exe` from Source

If you prefer to compile the standalone binary yourself instead of downloading the pre-built `.exe` from [GitHub Releases](https://github.com/Swif7ify/8BitDo-Battery-Tray-Display/releases):

To build it yourself from source:
1. Open PowerShell in the project directory.
2. Run:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass
   .\build.ps1
   ```
3. The standalone binary will be created in `dist\8BitDoBatteryTray.exe`.

---

## Tray Controls & Behavior

| Action | Result |
|---|---|
| **Hover on Tray Icon** | Displays tooltip with battery level, charging state, and connection mode. |
| **Right-Click Icon** | Opens context menu with live status summary, **Refresh now**, **Open log**, and **Exit**. |
| **Double-Click Icon / Refresh** | Forces an immediate battery query cycle instead of waiting for the 10-second timer. |

---

## Log File Location

Application logs are stored locally in:
```
%LOCALAPPDATA%\8BitDoBatteryTray\app.log
```
- Maximum file size: 256 KB (rotated once to keep disk usage under 512 KB total).
- No sensitive user data or game telemetry is ever logged.
