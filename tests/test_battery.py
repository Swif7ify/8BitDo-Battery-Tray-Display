from __future__ import annotations

from unittest.mock import MagicMock

from eightbitdo_battery_tray.battery import (
    TARGET_VID,
    WindowsGamingInputBatteryProvider,
)


class DummyController:
    def __init__(
        self,
        vid: int,
        pid: int,
        name: str = "Test Device",
        report: object | None = None,
    ) -> None:
        self.hardware_vendor_id = vid
        self.hardware_product_id = pid
        self.display_name = name
        self._report = report

    def try_get_battery_report(self) -> object | None:
        return self._report


class DummyBatteryReport:
    def __init__(
        self,
        remaining: int | None,
        full: int | None,
        charge_rate: int | None = None,
        status: int | None = None,
    ) -> None:
        self.remaining_capacity_in_milliwatt_hours = remaining
        self.full_charge_capacity_in_milliwatt_hours = full
        self.charge_rate_in_milliwatts = charge_rate
        self.status = status


def test_find_target_filtering() -> None:
    ctrl_xbox = DummyController(0x045E, 0x028E, "Xbox 360 Controller")
    ctrl_sony = DummyController(0x054C, 0x0CE6, "DualSense")
    ctrl_8bitdo_xinput = DummyController(TARGET_VID, 0x310B, "8BitDo Ultimate 2 XInput")
    ctrl_8bitdo_dinput = DummyController(TARGET_VID, 0x6012, "8BitDo Ultimate 2 DInput")

    # Empty list
    assert WindowsGamingInputBatteryProvider._find_target([]) is None

    # Other controllers only
    assert WindowsGamingInputBatteryProvider._find_target([ctrl_xbox, ctrl_sony]) is None

    # Target present
    found_xinput = WindowsGamingInputBatteryProvider._find_target([ctrl_xbox, ctrl_8bitdo_xinput])
    assert found_xinput is ctrl_8bitdo_xinput

    found_dinput = WindowsGamingInputBatteryProvider._find_target([ctrl_8bitdo_dinput, ctrl_sony])
    assert found_dinput is ctrl_8bitdo_dinput


def test_find_target_fault_tolerance() -> None:
    class FaultyController:
        @property
        def hardware_vendor_id(self) -> int:
            raise RuntimeError("Device disconnected")

        @property
        def hardware_product_id(self) -> int:
            return 0x310B

    valid = DummyController(TARGET_VID, 0x310B)
    result = WindowsGamingInputBatteryProvider._find_target([FaultyController(), valid])
    assert result is valid


def test_is_charging_detection() -> None:
    report_charging_rate = DummyBatteryReport(500, 1000, charge_rate=250)
    assert WindowsGamingInputBatteryProvider._is_charging(report_charging_rate) is True

    report_discharging_rate = DummyBatteryReport(500, 1000, charge_rate=-150)
    assert WindowsGamingInputBatteryProvider._is_charging(report_discharging_rate) is False

    report_status_charging = DummyBatteryReport(500, 1000, charge_rate=None, status=3)
    assert WindowsGamingInputBatteryProvider._is_charging(report_status_charging) is True

    report_status_discharging = DummyBatteryReport(500, 1000, charge_rate=None, status=1)
    assert WindowsGamingInputBatteryProvider._is_charging(report_status_discharging) is False


def test_read_with_mocked_provider() -> None:
    provider = WindowsGamingInputBatteryProvider()

    # Case 1: Controller not found
    provider._controllers = MagicMock(return_value=[])  # type: ignore[method-assign]
    snap1 = provider.read()
    assert snap1.connected is False
    assert snap1.percentage is None

    # Case 2: Controller found with valid battery report
    report = DummyBatteryReport(850, 1000, charge_rate=None, status=3)
    ctrl = DummyController(TARGET_VID, 0x310B, "8BitDo Ultimate 2", report=report)
    provider._controllers = MagicMock(return_value=[ctrl])  # type: ignore[method-assign]
    snap2 = provider.read()
    assert snap2.connected is True
    assert snap2.percentage == 85
    assert snap2.charging is True
    assert snap2.vendor_id == TARGET_VID
    assert snap2.product_id == 0x310B

    # Case 3: Controller found but Windows does not expose numeric capacities
    ctrl_no_capacity = DummyController(
        TARGET_VID, 0x310B, "8BitDo Ultimate 2", report=DummyBatteryReport(None, None)
    )
    provider._controllers = MagicMock(return_value=[ctrl_no_capacity])  # type: ignore[method-assign]
    snap3 = provider.read()
    assert snap3.connected is True
    assert snap3.percentage is None
