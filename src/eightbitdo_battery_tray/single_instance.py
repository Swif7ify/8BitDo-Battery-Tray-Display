from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Self

ERROR_ACCESS_DENIED = 5
ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = r"Local\EightBitDoUltimate2BatteryTray_v1"


class SingleInstance:
    """Per-Windows-session single-instance guard using a named mutex."""

    def __init__(self, name: str = MUTEX_NAME) -> None:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = (wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR)
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        kernel32.ReleaseMutex.argtypes = (wintypes.HANDLE,)
        kernel32.ReleaseMutex.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL

        self._kernel32 = kernel32
        self._handle = kernel32.CreateMutexW(None, True, name)
        last_error = ctypes.get_last_error()

        if not self._handle:
            if last_error == ERROR_ACCESS_DENIED:
                # Mutex already exists under another privilege level in the same session.
                self.already_running = True
                self._owns_mutex = False
                return
            raise ctypes.WinError(last_error)

        self.already_running = last_error == ERROR_ALREADY_EXISTS
        self._owns_mutex = not self.already_running

        if self.already_running:
            kernel32.CloseHandle(self._handle)
            self._handle = None

    def close(self) -> None:
        handle = self._handle
        if not handle:
            return

        if self._owns_mutex:
            self._kernel32.ReleaseMutex(handle)
        self._kernel32.CloseHandle(handle)
        self._handle = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
