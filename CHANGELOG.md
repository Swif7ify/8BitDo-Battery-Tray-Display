# Changelog

All notable changes to the **8BitDo Ultimate 2 Battery Tray** application are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-17

### Initial Release
- **Wide Landscape Transparent Battery Tray Icon**:
  - Designed in an ultra-wide horizontal landscape aspect ratio with a transparent background that fills the Windows taskbar slot.
  - Multi-directional dark outline guarantees high-contrast visibility on both dark and light taskbar themes.
  - High-luminance, ultra-bold numbers using Arial Black / Impact font rendering.
- **Smart Dual-Mode Battery Display**:
  - **Bluetooth Dual-Mode (Exact %)**: Displays the bold numeric percentage (e.g. `88%`) centered inside the wide battery, color-coded to the charge level (Electric Green for high, Amber for medium, Red for low, Cyan for charging).
  - **2.4 GHz Coarse Mode (Segments)**: Displays 3 capacity blocks inside the wide horizontal battery when running purely over the 2.4 GHz USB adapter.
  - ⚡ **Electric Cyan Lightning Bolt**: Overlays across the battery when charging.
  - ⚪ **Muted Neutral Cross**: Clean disconnected / sleep indicator.
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
