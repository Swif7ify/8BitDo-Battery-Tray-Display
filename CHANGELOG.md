# Changelog

All notable changes to the **8BitDo Ultimate 2 Battery Tray** application are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-17

### Initial Release
- **Windows-Style Transparent Battery Tray Icon**:
  - Full-width horizontal battery geometry that cleanly fills the Windows taskbar slot.
  - Multi-directional dark outline guarantees high-contrast visibility on both dark and light taskbar themes.
  - Smooth continuous capacity fill bar (matching native Windows battery behavior), color-coded by charge level (Electric Green, Amber, Orange, and Red).
  - ⚡ **Charging Indicator**: Bright white lightning bolt with dark outline overlays the battery when charging.
  - ⚪ **Muted Neutral Cross**: Clean disconnected / sleep indicator.
  - Hover tooltip displays the exact percentage, connection type, and charging state.
- **Custom Application Icon & Metadata**:
  - Embedded multi-resolution `logo.ico` and version information for OneDevPH into `8BitDoBatteryTray.exe`.
  - Authenticode code signing with RFC 3161 timestamping.
- **Accurate Bluetooth LE & 2.4 GHz Providers**:
  - Native Windows `cfgmgr32` Bluetooth LE GATT Battery Service gauge reading (`PKEY_Device_BatteryPercentage`).
  - Fallback to Windows Gaming Input for 2.4 GHz USB wireless receiver mode (`USB\VID_2DC8&PID_310B` / `0x6012`).
  - Read-only monitoring (zero HID writes).
- **Tray UI & Diagnostics**:
  - Real-time connection status in dynamic context menu and tooltips.
  - Single-instance named mutex protection.
  - Per-Monitor V2 DPI awareness.
  - Diagnostic CLI (`--once`, `diagnose.bat`).
  - Comprehensive unit test suite.
