from __future__ import annotations

import logging
import platform
import time
from collections.abc import Iterable
from typing import Any

from .model import BatterySnapshot, calculate_percentage

LOGGER = logging.getLogger(__name__)

# 8BitDo vendor ID.
TARGET_VID = 0x2DC8

# Ultimate 2 Wireless over the 2.4 GHz receiver:
#   0x310B = XInput mode
#   0x6012 = DInput mode
# We intentionally do not match Switch mode because it presents as a Nintendo
# controller and community testing reports unreliable battery reporting there.
TARGET_PIDS = frozenset({0x310B, 0x6012})


class WindowsGamingInputBatteryProvider:
    """Read battery information through Windows.Gaming.Input only.

    This class deliberately does not open HID handles, send feature reports,
    write output reports, switch controller modes, vibrate the controller, or
    modify firmware/configuration.
    """

    def __init__(self) -> None:
        if platform.system() != "Windows":
            raise RuntimeError("This application supports Windows only.")

        try:
            # Imported lazily so pure unit tests can run on non-Windows hosts.
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
        except (OSError, RuntimeError, AttributeError) as exc:  # WinRT can fail transiently
            LOGGER.warning("Windows battery query failed: %s", type(exc).__name__)
            return BatterySnapshot(
                connected=True,
                percentage=None,
                charging=None,
                device_name=name,
                vendor_id=vid,
                product_id=pid,
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
            detail="Battery percentage supplied by Windows Gaming Input.",
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
                # Device can disappear between enumeration and property access.
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
            # WinRT property access may fail transiently on disconnect/reconnect.
            return None
