from __future__ import annotations

import logging
import threading
from collections.abc import Callable

from .battery import WindowsGamingInputBatteryProvider
from .model import BatterySnapshot

LOGGER = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 10.0


class BatteryMonitor:
    """Low-frequency worker that never busy-waits."""

    def __init__(
        self,
        provider: WindowsGamingInputBatteryProvider,
        on_update: Callable[[BatterySnapshot], None],
        interval_seconds: float = POLL_INTERVAL_SECONDS,
    ) -> None:
        if interval_seconds < 1.0:
            raise ValueError("Polling below one second is intentionally unsupported.")

        self._provider = provider
        self._on_update = on_update
        self._interval = interval_seconds
        self._stop_event = threading.Event()
        self._refresh_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="8BitDoBatteryMonitor",
            daemon=True,
        )

    def start(self) -> None:
        self._thread.start()

    def refresh_now(self) -> None:
        self._refresh_event.set()

    def stop(self) -> None:
        self._stop_event.set()
        self._refresh_event.set()

    def join(self, timeout: float = 2.0) -> None:
        if self._thread.is_alive():
            self._thread.join(timeout=timeout)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                snapshot = self._provider.read()
                self._on_update(snapshot)
            except Exception:
                # Never crash the tray because a controller disappeared mid-query.
                LOGGER.exception("Unexpected battery monitor error")
                self._on_update(
                    BatterySnapshot(
                        connected=False,
                        percentage=None,
                        detail="Battery monitor encountered a recoverable error.",
                    )
                )

            # If Refresh is clicked while a read is in progress, wait() returns
            # immediately so that request is not lost.
            self._refresh_event.wait(self._interval)
            self._refresh_event.clear()
