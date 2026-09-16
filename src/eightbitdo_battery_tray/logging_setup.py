from __future__ import annotations

import logging
import os
import tempfile
from logging.handlers import RotatingFileHandler
from pathlib import Path

APP_DIR_NAME = "8BitDoBatteryTray"


def configure_logging() -> Path:
    """Configure tiny local-only logs; no telemetry or network output."""
    handler: RotatingFileHandler | None = None
    log_file: Path | None = None

    try:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        log_dir = base / APP_DIR_NAME
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
        handler = RotatingFileHandler(
            log_file,
            maxBytes=256 * 1024,
            backupCount=2,
            encoding="utf-8",
        )
    except OSError:
        base = Path(tempfile.gettempdir()) / APP_DIR_NAME
        base.mkdir(parents=True, exist_ok=True)
        log_file = base / "app.log"
        handler = RotatingFileHandler(
            log_file,
            maxBytes=256 * 1024,
            backupCount=2,
            encoding="utf-8",
        )

    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)
    return log_file
