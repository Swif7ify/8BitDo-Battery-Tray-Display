from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .model import BatteryLevel

ICON_SIZE = 64

_LEVEL_COLORS: dict[BatteryLevel, tuple[int, int, int, int]] = {
    BatteryLevel.EMPTY: (235, 75, 75, 255),
    BatteryLevel.LOW: (245, 125, 50, 255),
    BatteryLevel.MEDIUM: (245, 190, 55, 255),
    BatteryLevel.FULL: (70, 210, 120, 255),
    BatteryLevel.UNKNOWN: (150, 150, 160, 255),
}

_LEVEL_SEGMENTS: dict[BatteryLevel, int] = {
    BatteryLevel.EMPTY: 0,
    BatteryLevel.LOW: 1,
    BatteryLevel.MEDIUM: 2,
    BatteryLevel.FULL: 3,
    BatteryLevel.UNKNOWN: 0,
}


def percentage_to_level(pct: int | None) -> BatteryLevel:
    """Convert an integer percentage into a coarse 3-tier BatteryLevel."""
    if pct is None:
        return BatteryLevel.UNKNOWN
    if pct <= 15:
        return BatteryLevel.EMPTY
    if pct <= 30:
        return BatteryLevel.LOW
    if pct <= 70:
        return BatteryLevel.MEDIUM
    return BatteryLevel.FULL


@lru_cache(maxsize=64)
def make_icon(
    level: BatteryLevel | int | str | None = None,
    *,
    connected: bool = True,
    charging: bool = False,
    show_number: bool | None = None,
) -> Image.Image:
    """Create a maximum-size, transparent Windows tray icon.

    Displays either an enlarged numeric percentage (Bluetooth LE dual mode)
    or maximum-size vertical capacity blocks (2.4 GHz coarse mode).
    """
    pct: int | None = None
    bat_level: BatteryLevel = BatteryLevel.FULL

    if isinstance(level, int):
        pct = max(0, min(100, level))
        bat_level = percentage_to_level(pct)
        if show_number is None:
            show_number = True
    elif isinstance(level, str):
        if level == "--":
            connected = False
            bat_level = BatteryLevel.UNKNOWN
            show_number = False
        else:
            try:
                pct = int(level.rstrip("%"))
                bat_level = percentage_to_level(pct)
                if show_number is None:
                    show_number = True
            except ValueError:
                bat_level = (
                    BatteryLevel(level)
                    if level in BatteryLevel._value2member_map_
                    else BatteryLevel.UNKNOWN
                )
                show_number = False
    elif isinstance(level, BatteryLevel):
        bat_level = level
        show_number = False
    elif level is None:
        bat_level = BatteryLevel.UNKNOWN if connected else BatteryLevel.EMPTY
        show_number = False

    # Fully transparent canvas
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    neutral = (135, 138, 145, 255)

    if not connected:
        color = neutral
    elif charging:
        color = (70, 195, 245, 255)  # Electric Cyan
    else:
        color = _LEVEL_COLORS[bat_level]

    if not connected:
        _draw_disconnected(draw)
        return image

    _draw_enlarged_battery(
        draw=draw,
        level=bat_level,
        color=color,
        percentage=pct if show_number else None,
    )

    if charging:
        _draw_charge_symbol(draw)

    return image


def _draw_enlarged_battery(
    draw: ImageDraw.ImageDraw,
    level: BatteryLevel,
    color: tuple[int, int, int, int],
    percentage: int | None = None,
) -> None:
    """Draw the battery shell maximized across the canvas."""
    body = (1, 2, 56, 61)
    terminal = (57, 18, 63, 45)
    shell_color = (245, 248, 255, 255)

    # Dark drop outline for crisp contrast on light/dark taskbars
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1))
    for dx, dy in offsets:
        draw.rounded_rectangle(
            (body[0] + dx, body[1] + dy, body[2] + dx, body[3] + dy),
            radius=8,
            outline=(10, 10, 15, 240),
            width=4,
        )
        draw.rounded_rectangle(
            (terminal[0] + dx, terminal[1] + dy, terminal[2] + dx, terminal[3] + dy),
            radius=3,
            fill=(10, 10, 15, 240),
        )

    # Battery shell
    draw.rounded_rectangle(body, radius=8, outline=shell_color, width=3)
    draw.rounded_rectangle(terminal, radius=3, fill=shell_color)

    # If exact percentage is requested, draw maximum-size bold number inside
    if percentage is not None:
        label = str(percentage)
        font = _font_for(label)
        bbox = draw.textbbox((0, 0), label, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = 28 - (w / 2) - bbox[0]
        y = 31 - (h / 2) - bbox[1]

        # Dark halo under text for maximum legibility
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
            draw.text((x + dx, y + dy), label, font=font, fill=(10, 10, 15, 230))
        draw.text((x, y), label, font=font, fill=color)
        return

    # Otherwise draw 3 maximized vertical capacity blocks
    segments = _LEVEL_SEGMENTS[level]

    if level is BatteryLevel.UNKNOWN:
        font = _cached_font(32)
        bbox = draw.textbbox((0, 0), "?", font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = 28 - (w / 2) - bbox[0]
        y = 31 - (h / 2) - bbox[1]
        draw.text((x, y), "?", font=font, fill=color)
        return

    segment_boxes = (
        (8, 9, 20, 54),
        (24, 9, 36, 54),
        (40, 9, 52, 54),
    )

    inactive = (50, 55, 65, 180)

    for index, box in enumerate(segment_boxes):
        fill = color if index < segments else inactive
        draw.rounded_rectangle(box, radius=4, fill=fill)


def _draw_charge_symbol(draw: ImageDraw.ImageDraw) -> None:
    """Overlay a giant lightning symbol."""
    bolt = (
        (32, 6),
        (22, 29),
        (29, 29),
        (24, 56),
        (42, 24),
        (35, 24),
    )
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        draw.polygon([(bx + dx, by + dy) for bx, by in bolt], fill=(10, 10, 15, 220))
    draw.polygon(bolt, fill=(255, 255, 255, 255))


def _draw_disconnected(draw: ImageDraw.ImageDraw) -> None:
    """Draw a neutral disconnected battery with large diagonal cross."""
    body = (1, 2, 56, 61)
    terminal = (57, 18, 63, 45)
    draw.rounded_rectangle(body, radius=8, outline=(120, 125, 135, 200), width=3)
    draw.rounded_rectangle(terminal, radius=3, fill=(120, 125, 135, 200))
    draw.line((10, 10, 48, 53), fill=(140, 145, 155, 255), width=5)
    draw.line((48, 10, 10, 53), fill=(140, 145, 155, 255), width=5)


def _font_for(label: str) -> ImageFont.ImageFont:
    # Size 29 for 3 digits (100), size 42 for 1-2 digits (88)
    size = 29 if len(label) >= 3 else 42
    return _cached_font(size)


@lru_cache(maxsize=8)
def _cached_font(size: int) -> ImageFont.ImageFont:
    windows_dir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    candidates = (
        windows_dir / "Fonts" / "segoeuib.ttf",
        windows_dir / "Fonts" / "arialbd.ttf",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(str(path), size=size)
        except OSError:
            continue
    return ImageFont.load_default()
