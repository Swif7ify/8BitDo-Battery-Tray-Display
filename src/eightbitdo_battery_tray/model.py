from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BatterySnapshot:
    connected: bool
    percentage: int | None
    charging: bool | None = None
    device_name: str | None = None
    vendor_id: int | None = None
    product_id: int | None = None
    connection_type: str | None = None
    detail: str | None = None


def calculate_percentage(remaining: int | None, full: int | None) -> int | None:
    """Return a clamped 0..100 percentage, or None when capacity is unavailable."""
    if remaining is None or full is None or full <= 0 or remaining < 0:
        return None

    value = round((remaining / full) * 100)
    return max(0, min(100, value))
