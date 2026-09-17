from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BatteryLevel(StrEnum):
    EMPTY = "empty"
    LOW = "low"
    MEDIUM = "medium"
    FULL = "full"
    UNKNOWN = "unknown"


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


def estimate_remaining_hours(percentage: int | None) -> str | None:
    """Estimate remaining battery runtime based on 8BitDo Ultimate 2's ~18h rating.

    Returns a human-friendly string such as '~16h', '~1h 45m', or None if unavailable.
    """
    if percentage is None:
        return None
    pct = max(0, min(100, percentage))
    total_rated_hours = 18.0
    hours = (pct / 100.0) * total_rated_hours
    if hours >= 2.0:
        return f"~{int(round(hours))}h"
    if hours >= 1.0:
        mins = int(round(hours * 60))
        return f"~{mins // 60}h {mins % 60}m"
    mins = max(5, int(round(hours * 60)))
    return f"~{mins}m"
