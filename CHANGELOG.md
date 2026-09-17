# Changelog

All notable changes to the **8BitDo Ultimate 2 Battery Tray** application are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-09-17

### Added
- **Enlarged Transparent Battery Tray Icon**:
  - Removed dark background tile and small logo in favor of a clean, prominent battery icon with transparent background that seamlessly blends into the Windows taskbar.
  - Drop-shadow outline guarantees high-contrast visibility on both dark and light taskbar themes.
- **Smart Dual-Mode Battery Display**:
  - **Bluetooth Dual-Mode (Exact %)**: Displays the bold numeric percentage (e.g. `88%`) inside the battery, color-coded to the charge level (Green for high, Amber for medium, Red for low, Cyan for charging).
  - **2.4 GHz Coarse Mode (Segments)**: Displays 3 large vertical capacity blocks inside the battery when running purely over the 2.4 GHz USB adapter.
  - ⚡ **Electric Cyan Lightning Bolt**: Overlays across the battery when charging.
  - ⚪ **Muted Neutral Cross**: Clean disconnected / sleep indicator.
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
