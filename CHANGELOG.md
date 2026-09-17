# Changelog

All notable changes to the **8BitDo Ultimate 2 Battery Tray** application are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-09-17

### Added
- **Wide Landscape Transparent Battery Tray Icon**:
  - Designed in a horizontal landscape aspect ratio (wider in width, compact in height) with a transparent background that fits cleanly in the Windows taskbar.
  - Multi-directional dark outline guarantees high-contrast visibility on both dark and light taskbar themes.
- **Smart Dual-Mode Battery Display**:
  - **Bluetooth Dual-Mode (Exact %)**: Displays the bold numeric percentage (e.g. `88%`) centered inside the wide battery, color-coded to the charge level (Green for high, Amber for medium, Red for low, Cyan for charging).
  - **2.4 GHz Coarse Mode (Segments)**: Displays 3 capacity blocks inside the wide horizontal battery when running purely over the 2.4 GHz USB adapter.
  - ⚡ **Electric Cyan Lightning Bolt**: Overlays across the battery when charging.
  - ⚪ **Muted Neutral Cross**: Clean disconnected / sleep indicator.
- **Custom Application Icon**:
  - Automatically compiles `logo.png` into a multi-resolution `.ico` embedded into `8BitDoBatteryTray.exe` so the application has the custom 8BitDo battery logo in Windows Explorer, the taskbar, and task manager.
- **Accurate Bluetooth LE Battery Provider**:
  - Uses native Windows `cfgmgr32` to read `PKEY_Device_BatteryPercentage` directly from the Bluetooth LE GATT Battery Service.
  - Accurately reports true hardware battery percentage (e.g. `88%`).
- **Composite Battery Provider**:
  - Automatically queries Bluetooth LE first for exact gauge reporting.
  - Gracefully falls back to Windows Gaming Input for 2.4 GHz USB wireless receiver mode (`USB\VID_2DC8&PID_310B` / `0x6012`).
- **Dynamic Context Menu**: Right-click menu now displays real-time connection status (e.g., `● 8BitDo: 88% via Bluetooth LE`), manual refresh, log viewer, and clean exit.
- **Embedded Asset Bundling**: Bundled `logo.png`, `logo.ico`, and vector assets into the PyInstaller one-file distribution.
- **Automated Test Suite**: Added comprehensive unit tests covering icon generation, segment thresholds, composite provider priority, fallback logic, and single-instance mutex handling.

### Changed
- Improved tooltip display to include exact percentage, charging state, and active connection type.
- Updated `diagnose.bat` and `--once` CLI to output connection type and exact battery level.
- Refactored `icon_factory.py` to support wide horizontal battery geometry with high-contrast text and blocks.

---

## [1.0.0] - 2026-09-16

### Initial Release
- Read-only battery monitor for 8BitDo Ultimate 2 Wireless controllers.
- Polling via Windows Gaming Input (WGI) API.
- Single-instance named mutex protection.
- Per-Monitor V2 DPI awareness.
- Size-capped local logging in `%LOCALAPPDATA%`.
- Standalone single-file Windows executable build support (`build.ps1`).
