from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

import pystray
from pystray import Menu, MenuItem

from .battery import WindowsGamingInputBatteryProvider
from .icon_factory import make_icon
from .model import BatterySnapshot
from .monitor import BatteryMonitor

LOGGER = logging.getLogger(__name__)
APP_NAME = "8BitDo Ultimate 2 Battery"


class TrayApplication:
    def __init__(self, log_path: Path) -> None:
        self._log_path = log_path
        self._state_lock = threading.Lock()
        self._is_stopping = False
        self._snapshot = BatterySnapshot(connected=False, percentage=None)
        self._icon = pystray.Icon(
            name="8BitDoUltimate2Battery",
            icon=make_icon("--"),
            title=f"{APP_NAME} — checking…",
            menu=Menu(
                MenuItem("8BitDo Battery Tray — Running", self._on_noop, enabled=False),
                Menu.SEPARATOR,
                MenuItem("Refresh now", self._on_refresh, default=True),
                MenuItem("Open log", self._on_open_log),
                Menu.SEPARATOR,
                MenuItem("Exit", self._on_exit),
            ),
        )
        self._monitor = BatteryMonitor(
            provider=WindowsGamingInputBatteryProvider(),
            on_update=self._apply_snapshot,
        )

    def run(self) -> None:
        self._monitor.start()
        try:
            self._icon.run(setup=self._on_tray_ready)
        finally:
            with self._state_lock:
                self._is_stopping = True
            self._monitor.stop()
            self._monitor.join()

    def _on_tray_ready(self, icon: pystray.Icon) -> None:
        # pystray's default setup only sets icon.visible=True. Do that explicitly
        # so the lifecycle is obvious and we can issue a one-time startup notice.
        icon.visible = True
        try:
            icon.notify(
                "Running in the system tray. Right-click the icon for Refresh, Open log, or Exit.",
                APP_NAME,
            )
        except (OSError, RuntimeError) as exc:
            # Notifications are optional and may be disabled by Windows/Focus Assist.
            LOGGER.debug("Startup tray notification unavailable: %s", exc)

    def _apply_snapshot(self, snapshot: BatterySnapshot) -> None:
        with self._state_lock:
            if self._is_stopping:
                return
            self._snapshot = snapshot

        is_charging = bool(snapshot.charging)
        if snapshot.percentage is not None:
            icon_label = str(snapshot.percentage)
            charge_str = " (Charging)" if is_charging else ""
            title = f"{APP_NAME} — {snapshot.percentage}%{charge_str}"
        elif snapshot.connected:
            icon_label = "--"
            charge_str = " (Charging)" if is_charging else ""
            title = f"{APP_NAME} — percentage unavailable{charge_str}"
        else:
            icon_label = "--"
            title = f"{APP_NAME} — controller disconnected"

        LOGGER.info(
            "Controller update: connected=%s, percentage=%s, charging=%s",
            snapshot.connected,
            snapshot.percentage,
            snapshot.charging,
        )

        try:
            self._icon.icon = make_icon(icon_label, charging=is_charging)
            self._icon.title = title[:127]
            self._icon.update_menu()
        except (OSError, RuntimeError) as exc:
            LOGGER.debug("Tray icon update skipped: %s", exc)

    def _on_refresh(self, icon: pystray.Icon, item: MenuItem) -> None:
        del icon, item
        self._monitor.refresh_now()

    def _on_open_log(self, icon: pystray.Icon, item: MenuItem) -> None:
        del icon, item
        try:
            # os.startfile delegates to Windows' normal file association and does
            # not create a shell command string.
            os.startfile(self._log_path)  # noqa: S606  # type: ignore[attr-defined]
        except OSError:
            LOGGER.exception("Unable to open log file")

    def _on_exit(self, icon: pystray.Icon, item: MenuItem) -> None:
        del item
        with self._state_lock:
            self._is_stopping = True
        self._monitor.stop()
        icon.stop()

    @staticmethod
    def _on_noop(icon: pystray.Icon, item: MenuItem) -> None:
        del icon, item
