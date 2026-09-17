from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

import pystray
from pystray import Menu, MenuItem

from .battery import Composite8BitDoBatteryProvider
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
            icon=make_icon("--", connected=False),
            title=f"{APP_NAME} — checking…",
            menu=self._create_menu(),
        )
        self._monitor = BatteryMonitor(
            provider=Composite8BitDoBatteryProvider(),
            on_update=self._apply_snapshot,
        )

    def _create_menu(self) -> Menu:
        with self._state_lock:
            s = self._snapshot

        if s.connected:
            charge_str = " (Charging)" if s.charging else ""
            pct_str = f"{s.percentage}%" if s.percentage is not None else "Connected"
            conn_str = f" via {s.connection_type}" if s.connection_type else ""
            status_text = f"● 8BitDo: {pct_str}{charge_str}{conn_str}"
        else:
            status_text = "○ 8BitDo: Disconnected"

        return Menu(
            MenuItem(status_text, self._on_noop, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Refresh now", self._on_refresh, default=True),
            MenuItem("Open log", self._on_open_log),
            Menu.SEPARATOR,
            MenuItem("Exit", self._on_exit),
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
        icon.visible = True
        try:
            icon.notify(
                "Running in the system tray. Right-click the icon for Refresh, Open log, or Exit.",
                APP_NAME,
            )
        except (OSError, RuntimeError) as exc:
            LOGGER.debug("Startup tray notification unavailable: %s", exc)

    def _apply_snapshot(self, snapshot: BatterySnapshot) -> None:
        with self._state_lock:
            if self._is_stopping:
                return
            self._snapshot = snapshot

        is_charging = bool(snapshot.charging)
        conn_str = f" [{snapshot.connection_type}]" if snapshot.connection_type else ""
        if snapshot.percentage is not None:
            charge_str = " (Charging)" if is_charging else ""
            title = f"{APP_NAME} — {snapshot.percentage}%{charge_str}{conn_str}"
        elif snapshot.connected:
            charge_str = " (Charging)" if is_charging else ""
            title = f"{APP_NAME} — Connected{charge_str}{conn_str}"
        else:
            title = f"{APP_NAME} — Controller disconnected"

        LOGGER.info(
            "Controller update: connected=%s, percentage=%s, charging=%s, mode=%s",
            snapshot.connected,
            snapshot.percentage,
            snapshot.charging,
            snapshot.connection_type,
        )

        try:
            self._icon.icon = make_icon(
                level=snapshot.percentage,
                charging=is_charging,
                connected=snapshot.connected,
            )
            self._icon.title = title[:127]
            self._icon.menu = self._create_menu()
            self._icon.update_menu()
        except (OSError, RuntimeError) as exc:
            LOGGER.debug("Tray icon update skipped: %s", exc)

    def _on_refresh(self, icon: pystray.Icon, item: MenuItem) -> None:
        del icon, item
        self._monitor.refresh_now()

    def _on_open_log(self, icon: pystray.Icon, item: MenuItem) -> None:
        del icon, item
        try:
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
