from __future__ import annotations

import time
from unittest.mock import MagicMock

from eightbitdo_battery_tray.model import BatterySnapshot
from eightbitdo_battery_tray.monitor import BatteryMonitor


def test_battery_monitor_lifecycle() -> None:
    mock_provider = MagicMock()
    mock_provider.read.return_value = BatterySnapshot(connected=False, percentage=None)

    updates: list[BatterySnapshot] = []

    def on_update(snap: BatterySnapshot) -> None:
        updates.append(snap)

    monitor = BatteryMonitor(
        provider=mock_provider,
        on_update=on_update,
        interval_seconds=1.0,
    )

    monitor.start()
    # Give worker a moment to run first iteration
    time.sleep(0.1)
    assert len(updates) >= 1

    monitor.refresh_now()
    time.sleep(0.1)
    assert len(updates) >= 2

    monitor.stop()
    monitor.join(timeout=1.0)
    assert not monitor._thread.is_alive()
