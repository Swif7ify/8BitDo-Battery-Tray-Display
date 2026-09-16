from __future__ import annotations

import argparse
import ctypes
import platform
import sys
from pathlib import Path

from .logging_setup import configure_logging


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="8BitDo Ultimate 2 battery tray monitor")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Print one read-only battery query and exit (useful for diagnostics).",
    )
    return parser.parse_args()


def _print_once() -> int:
    from .battery import WindowsGamingInputBatteryProvider

    snapshot = WindowsGamingInputBatteryProvider().read()
    if not snapshot.connected:
        print("Controller: not detected")
        print(f"Detail: {snapshot.detail or 'n/a'}")
        return 2

    pid = f"0x{snapshot.product_id:04X}" if snapshot.product_id is not None else "unknown"
    print(f"Controller: {snapshot.device_name or '8BitDo Ultimate 2'}")
    print(f"VID/PID: 0x2DC8/{pid}")
    print(
        f"Battery: {snapshot.percentage}%"
        if snapshot.percentage is not None
        else "Battery: exact percentage not exposed by Windows"
    )
    print(f"Detail: {snapshot.detail or 'n/a'}")
    return 0 if snapshot.percentage is not None else 3


def _show_fatal_error(exc: Exception, log_path: Path) -> None:
    """Show startup failures even when running through pythonw.exe."""
    message = (
        "8BitDo Battery Tray could not start.\n\n"
        f"{type(exc).__name__}: {exc}\n\n"
        f"A diagnostic log was written to:\n{log_path}"
    )
    try:
        ctypes.windll.user32.MessageBoxW(None, message, "8BitDo Battery Tray", 0x10)
    except Exception:
        # There may still be a console when launched manually.
        if sys.stderr is not None:
            print(message, file=sys.stderr)


def main() -> int:
    if platform.system() != "Windows":
        print("This application supports Windows only.", file=sys.stderr)
        return 1

    log_path = configure_logging()
    args = _parse_args()

    if args.once:
        return _print_once()

    from .app import TrayApplication
    from .single_instance import SingleInstance

    try:
        with SingleInstance() as instance:
            if instance.already_running:
                return 0
            TrayApplication(log_path=log_path).run()
            return 0
    except Exception as exc:
        import logging

        logging.getLogger(__name__).exception("Fatal application error")
        _show_fatal_error(exc, log_path)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
