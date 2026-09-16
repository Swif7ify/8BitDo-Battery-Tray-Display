from eightbitdo_battery_tray.model import calculate_percentage


def test_percentage_nominal() -> None:
    assert calculate_percentage(750, 1000) == 75


def test_percentage_clamps_high() -> None:
    assert calculate_percentage(1050, 1000) == 100


def test_percentage_clamps_low_and_rejects_invalid() -> None:
    assert calculate_percentage(-1, 1000) is None
    assert calculate_percentage(1, 0) is None
    assert calculate_percentage(None, 1000) is None
    assert calculate_percentage(500, None) is None
