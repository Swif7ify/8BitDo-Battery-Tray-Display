import pytest

from eightbitdo_battery_tray.model import BatterySnapshot, calculate_percentage


def test_percentage_nominal() -> None:
    assert calculate_percentage(750, 1000) == 75


def test_percentage_clamps_high() -> None:
    assert calculate_percentage(1050, 1000) == 100


def test_percentage_clamps_low_and_rejects_invalid() -> None:
    assert calculate_percentage(-1, 1000) is None
    assert calculate_percentage(1, 0) is None
    assert calculate_percentage(None, 1000) is None
    assert calculate_percentage(500, None) is None


def test_battery_snapshot_immutability_and_defaults() -> None:
    snapshot = BatterySnapshot(
        connected=True,
        percentage=85,
        charging=True,
        device_name="8BitDo Ultimate 2",
        vendor_id=0x2DC8,
        product_id=0x310B,
        detail="OK",
    )
    assert snapshot.connected is True
    assert snapshot.percentage == 85
    assert snapshot.charging is True
    assert snapshot.device_name == "8BitDo Ultimate 2"
    assert snapshot.vendor_id == 0x2DC8
    assert snapshot.product_id == 0x310B
    assert snapshot.detail == "OK"

    with pytest.raises(AttributeError):
        snapshot.percentage = 90  # type: ignore[misc]


def test_estimate_remaining_hours() -> None:
    from eightbitdo_battery_tray.model import estimate_remaining_hours

    assert estimate_remaining_hours(None) is None
    assert estimate_remaining_hours(100) == "~18h"
    assert estimate_remaining_hours(88) == "~16h"
    assert estimate_remaining_hours(50) == "~9h"
    assert estimate_remaining_hours(25) == "~4h"
    assert estimate_remaining_hours(10) == "~1h 48m"
    assert estimate_remaining_hours(5) == "~54m"
    assert estimate_remaining_hours(0) == "~5m"
