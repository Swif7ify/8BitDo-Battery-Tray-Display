from __future__ import annotations

import argparse
import ctypes
import platform
import sys
from pathlib import Path

from .logging_setup import configure_logging


def _enable_dpi_awareness() -> None:
    """Enable Per-Monitor V2 DPI awareness for sharp rendering on high-DPI displays."""
    try:
        # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            # PROCESS_PER_MONITOR_DPI_AWARE = 2
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            pass


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

    vid = f"0x{snapshot.vendor_id:04X}" if snapshot.vendor_id is not None else "0x2DC8"
    pid = f"0x{snapshot.product_id:04X}" if snapshot.product_id is not None else "unknown"
    charge_suffix = " (Charging)" if snapshot.charging else ""
    print(f"Controller: {snapshot.device_name or '8BitDo Ultimate 2'}")
    print(f"VID/PID: {vid}/{pid}")
    print(
        f"Battery: {snapshot.percentage}%{charge_suffix}"
        if snapshot.percentage is not None
        else f"Battery: exact percentage not exposed by Windows{charge_suffix}"
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
    except (AttributeError, OSError):
        # There may still be a console when launched manually.
        if sys.stderr is not None:
            print(message, file=sys.stderr)


def _attach_console_if_needed() -> None:
    """Attach to the parent console if launched from a terminal in windowed mode."""
    try:
        # ATTACH_PARENT_PROCESS = -1
        if ctypes.windll.kernel32.AttachConsole(-1):
            if sys.stdout is None or not hasattr(sys.stdout, "write"):
                sys.stdout = open("CONOUT$", "w", encoding="utf-8")  # noqa: SIM115
            if sys.stderr is None or not hasattr(sys.stderr, "write"):
                sys.stderr = open("CONOUT$", "w", encoding="utf-8")  # noqa: SIM115
    except (AttributeError, OSError):
        pass


def main() -> int:
    if platform.system() != "Windows":
        print("This application supports Windows only.", file=sys.stderr)
        return 1

    _enable_dpi_awareness()
    log_path = configure_logging()
    args = _parse_args()

    if args.once:
        _attach_console_if_needed()
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
