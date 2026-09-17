from __future__ import annotations

import ctypes
import logging
import platform
import time
from collections.abc import Iterable
from ctypes import Structure, byref, c_byte, c_ulong, create_unicode_buffer, wintypes
from typing import Any

from .model import BatterySnapshot, calculate_percentage

LOGGER = logging.getLogger(__name__)

# 8BitDo vendor ID.
TARGET_VID = 0x2DC8

# Ultimate 2 Wireless over the 2.4 GHz receiver:
#   0x310B = XInput mode
#   0x6012 = DInput mode
TARGET_PIDS = frozenset({0x310B, 0x6012})

# SetupAPI / CfgMgr32 DEVPROPKEY definition
class _GUID(Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", c_byte * 8),
    ]


class _DEVPROPKEY(Structure):
    _fields_ = [("fmtid", _GUID), ("pid", wintypes.ULONG)]


# Standard Windows Device Property Keys:
# DEVPKEY_NAME: {B725F130-47EF-101A-A5F1-02608C9EEBAC}, 10
_PKEY_NAME = _DEVPROPKEY(
    _GUID(0xB725F130, 0x47EF, 0x101A, (c_byte * 8)(0xA5, 0xF1, 0x02, 0x60, 0x8C, 0x9E, 0xEB, 0xAC)),
    10,
)
# DEVPKEY_Device_BatteryPercentage: {104EA319-6EE2-4701-BD47-8DDBF425BBE5}, 2
_PKEY_BATT = _DEVPROPKEY(
    _GUID(0x104EA319, 0x6EE2, 0x4701, (c_byte * 8)(0xBD, 0x47, 0x8D, 0xDB, 0xF4, 0x25, 0xBB, 0xE5)),
    2,
)

_CR_SUCCESS = 0
_DN_STARTED = 0x00000008


class WindowsBluetoothBatteryProvider:
    """Read the exact hardware battery percentage of 8BitDo controllers over Bluetooth LE.

    When paired over Bluetooth LE, 8BitDo controllers expose the standard Bluetooth
    Battery Service (GATT 0x180F). Windows natively queries this and caches the true
    hardware gauge byte in DEVPKEY_Device_BatteryPercentage.
    """

    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise RuntimeError("This application supports Windows only.")
        try:
            self._cfgmgr32 = ctypes.WinDLL("cfgmgr32")
        except OSError as exc:
            raise RuntimeError("Unable to load cfgmgr32.dll on this system.") from exc

    def read(self) -> BatterySnapshot:
        """Scan active Bluetooth devices for an 8BitDo controller."""
        buf_len = c_ulong(0)
        res = self._cfgmgr32.CM_Get_Device_ID_List_SizeW(byref(buf_len), None, 0)
        if res != _CR_SUCCESS or buf_len.value == 0:
            return BatterySnapshot(
                connected=False,
                percentage=None,
                detail="Unable to enumerate system devices via cfgmgr32.",
            )

        buf = create_unicode_buffer(buf_len.value)
        res = self._cfgmgr32.CM_Get_Device_ID_ListW(None, buf, buf_len.value, 0)
        if res != _CR_SUCCESS:
            return BatterySnapshot(
                connected=False,
                percentage=None,
                detail="Unable to read device ID list.",
            )

        for dev_id in buf[:].split("\0"):
            if not dev_id:
                continue

            devinst = wintypes.DWORD()
            if self._cfgmgr32.CM_Locate_DevNodeW(byref(devinst), dev_id, 0) != _CR_SUCCESS:
                continue

            # Read Device Friendly Name
            prop_type = c_ulong()
            name_buf = create_unicode_buffer(512)
            name_size = c_ulong(ctypes.sizeof(name_buf))
            r = self._cfgmgr32.CM_Get_DevNode_PropertyW(
                devinst, byref(_PKEY_NAME), byref(prop_type), name_buf, byref(name_size), 0
            )
            if r != _CR_SUCCESS:
                continue

            device_name = name_buf.value
            if "8bitdo" not in device_name.lower():
                continue

            # Check if device is actively started/connected
            status = wintypes.DWORD()
            problem = wintypes.DWORD()
            r = self._cfgmgr32.CM_Get_DevNode_Status(byref(status), byref(problem), devinst, 0)
            is_started = (r == _CR_SUCCESS) and bool(status.value & _DN_STARTED)

            if not is_started:
                continue

            # Query battery percentage
            batt_byte = c_byte()
            batt_size = c_ulong(ctypes.sizeof(batt_byte))
            r = self._cfgmgr32.CM_Get_DevNode_PropertyW(
                devinst, byref(_PKEY_BATT), byref(prop_type), byref(batt_byte), byref(batt_size), 0
            )

            pct: int | None = None
            if r == _CR_SUCCESS and 0 <= batt_byte.value <= 100:
                pct = int(batt_byte.value)

            return BatterySnapshot(
                connected=True,
                percentage=pct,
                device_name=device_name,
                connection_type="Bluetooth LE",
                detail="Battery percentage supplied by Bluetooth LE (accurate hardware gauge).",
            )

        return BatterySnapshot(
            connected=False,
            percentage=None,
            detail="8BitDo controller not detected via Bluetooth LE.",
        )


class WindowsGamingInputBatteryProvider:
    """Read battery information through Windows.Gaming.Input (2.4 GHz USB Dongle).

    This class deliberately does not open HID handles, send feature reports,
    write output reports, switch controller modes, vibrate the controller, or
    modify firmware/configuration.
    """

    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise RuntimeError("This application supports Windows only.")

        try:
            from winrt.windows.gaming.input import RawGameController
        except ImportError as exc:  # pragma: no cover - Windows dependency path
            raise RuntimeError(
                "Windows Gaming Input support is not installed. Run: pip install -e ."
            ) from exc

        self._raw_game_controller = RawGameController
        self._first_enumeration = True

    def read(self) -> BatterySnapshot:
        controllers = self._controllers()
        target = self._find_target(controllers)
        if target is None:
            return BatterySnapshot(
                connected=False,
                percentage=None,
                detail="8BitDo Ultimate 2 not detected in 2.4 GHz XInput/DInput mode.",
            )

        name = self._safe_attr(target, "display_name")
        vid = self._safe_int_attr(target, "hardware_vendor_id")
        pid = self._safe_int_attr(target, "hardware_product_id")

        try:
            report = target.try_get_battery_report()
        except (OSError, RuntimeError, AttributeError) as exc:
            LOGGER.warning("Windows battery query failed: %s", type(exc).__name__)
            return BatterySnapshot(
                connected=True,
                percentage=None,
                charging=None,
                device_name=name,
                vendor_id=vid,
                product_id=pid,
                connection_type="2.4GHz Wireless",
                detail="Controller detected, but Windows did not return a battery report.",
            )

        if report is None:
            return BatterySnapshot(
                connected=True,
                percentage=None,
                charging=None,
                device_name=name,
                vendor_id=vid,
                product_id=pid,
                connection_type="2.4GHz Wireless",
                detail="Controller detected, but Windows exposes no battery report in this mode.",
            )

        remaining = self._safe_int_attr(report, "remaining_capacity_in_milliwatt_hours")
        full = self._safe_int_attr(report, "full_charge_capacity_in_milliwatt_hours")
        percentage = calculate_percentage(remaining, full)
        charging = self._is_charging(report)

        if percentage is None:
            return BatterySnapshot(
                connected=True,
                percentage=None,
                charging=charging,
                device_name=name,
                vendor_id=vid,
                product_id=pid,
                connection_type="2.4GHz Wireless",
                detail=(
                    "Controller detected, but Windows does not expose numeric remaining/full "
                    "battery capacity in this mode."
                ),
            )

        return BatterySnapshot(
            connected=True,
            percentage=percentage,
            charging=charging,
            device_name=name,
            vendor_id=vid,
            product_id=pid,
            connection_type="2.4GHz Wireless",
            detail="Battery level supplied by Windows Gaming Input (2.4 GHz receiver).",
        )

    def _controllers(self) -> list[Any]:
        """Enumerate controllers, allowing WGI a short one-time warm-up."""
        attempts = 4 if self._first_enumeration else 1
        self._first_enumeration = False

        last: list[Any] = []
        for attempt in range(attempts):
            try:
                last = list(self._raw_game_controller.raw_game_controllers)
            except (OSError, RuntimeError, AttributeError) as exc:
                LOGGER.warning("Controller enumeration failed: %s", type(exc).__name__)
                return []

            if last or attempt == attempts - 1:
                return last
            time.sleep(0.15)
        return last

    @staticmethod
    def _find_target(controllers: Iterable[Any]) -> Any | None:
        for controller in controllers:
            try:
                vid = int(controller.hardware_vendor_id)
                pid = int(controller.hardware_product_id)
            except (OSError, RuntimeError, AttributeError, ValueError) as exc:
                LOGGER.debug("Target property access skipped: %s", exc)
                continue

            if vid == TARGET_VID and pid in TARGET_PIDS:
                return controller
        return None

    @staticmethod
    def _is_charging(report: Any) -> bool | None:
        """Detect charging state from charge rate or status property."""
        rate = WindowsGamingInputBatteryProvider._safe_int_attr(
            report, "charge_rate_in_milliwatts"
        )
        if rate is not None:
            if rate > 0:
                return True
            if rate < 0:
                return False

        try:
            status = getattr(report, "status", None)
            if status is not None:
                status_int = int(status)
                if status_int == 3:  # BatteryStatus.Charging
                    return True
                if status_int in (1, 2):  # Discharging, Idle
                    return False
        except (AttributeError, RuntimeError, OSError, ValueError, TypeError, ModuleNotFoundError):
            pass
        return None

    @staticmethod
    def _safe_attr(obj: Any, name: str) -> str | None:
        try:
            value = getattr(obj, name)
        except (AttributeError, RuntimeError, OSError, ModuleNotFoundError):
            return None
        return str(value) if value is not None else None

    @staticmethod
    def _safe_int_attr(obj: Any, name: str) -> int | None:
        try:
            value = getattr(obj, name)
            return None if value is None else int(value)
        except (AttributeError, RuntimeError, OSError, ValueError, TypeError, ModuleNotFoundError):
            return None


class Composite8BitDoBatteryProvider:
    """Composite provider prioritizing Bluetooth LE with 2.4 GHz fallback."""

    def __init__(self) -> None:
        self._bt_provider = WindowsBluetoothBatteryProvider()
        self._wgi_provider = WindowsGamingInputBatteryProvider()

    def read(self) -> BatterySnapshot:
        # 1. Try Bluetooth LE first (provides accurate hardware gauge e.g. 88%)
        try:
            bt_snapshot = self._bt_provider.read()
            if bt_snapshot.connected:
                return bt_snapshot
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("Bluetooth provider query failed: %s", exc)

        # 2. Try 2.4 GHz receiver via Windows Gaming Input
        try:
            wgi_snapshot = self._wgi_provider.read()
            if wgi_snapshot.connected:
                return wgi_snapshot
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("Windows Gaming Input query failed: %s", exc)

        # 3. Not detected in either mode
        return BatterySnapshot(
            connected=False,
            percentage=None,
            detail="8BitDo controller not detected via Bluetooth or 2.4 GHz wireless.",
        )


EightBitDoBatteryProvider = Composite8BitDoBatteryProvider
