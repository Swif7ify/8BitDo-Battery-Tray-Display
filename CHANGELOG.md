# Changelog

All notable changes to the **8BitDo Ultimate 2 Battery Tray** application are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-09-17

### Added
- **Official 8BitDo Branding**: System tray icon now displays the official 8BitDo logo on a sleek dark slate tile.
- **Color-Coded Battery Checker**:
  - Replaced plain text numbers with a 4-segment hardware battery meter and state-glowing tile outline.
  - ⚡ **Electric Cyan with Lightning Bolt**: Controller is actively charging (docked or USB-C).
  - 🟢 **Vivid Emerald Green (4 bars)**: Good / High battery capacity ($> 50\%$).
  - 🟡 **Warm Amber (2 bars)**: Medium battery level ($21\% - 50\%$).
  - 🔴 **Alert Red (1 bar)**: Low battery warning ($\le 20\%$).
  - ⚪ **Muted Slate Gray (Offline Dot)**: Disconnected / sleep mode.
- **Accurate Bluetooth LE Battery Provider**:
  - Uses native Windows `cfgmgr32` to read `PKEY_Device_BatteryPercentage` directly from the Bluetooth LE GATT Battery Service.
  - Accurately reports true hardware battery percentage (e.g. `88%`).
- **Composite Battery Provider**:
  - Automatically queries Bluetooth LE first for exact gauge reporting.
  - Gracefully falls back to Windows Gaming Input for 2.4 GHz USB wireless receiver mode (`USB\VID_2DC8&PID_310B` / `0x6012`).
- **Dynamic Context Menu**: Right-click menu now displays real-time connection status (e.g., `● 8BitDo: 88% via Bluetooth LE`), manual refresh, log viewer, and clean exit.
- **Embedded Asset Bundling**: Bundled `8bitdo_logo_white.png` and `8bitdo_logo.svg` into PyInstaller one-file distribution.
- **Automated Test Suite**: Added 20 comprehensive unit tests covering icon generation, segment thresholds, composite provider priority, fallback logic, and single-instance mutex handling.

### Changed
- Improved tooltip display to include exact percentage, charging state, and active connection type.
- Updated `diagnose.bat` and `--once` CLI to output connection type and exact battery level.
- Refactored `icon_factory.py` to support high-contrast color badges with automatic asset fallback.

---

## [1.0.0] - 2026-09-16

### Initial Release
- Read-only battery monitor for 8BitDo Ultimate 2 Wireless controllers.
- Polling via Windows Gaming Input (WGI) API.
- Single-instance named mutex protection.
- Per-Monitor V2 DPI awareness.
- Size-capped local logging in `%LOCALAPPDATA%`.
- Standalone single-file Windows executable build support (`build.ps1`).
