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
    """Create a large, transparent Windows tray icon.

    Displays either an exact percentage number (e.g. from Bluetooth LE dual mode)
    or large vertical capacity blocks (e.g. from 2.4 GHz coarse mode).
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
    """Draw the central battery symbol enlarged across the canvas without dark tile."""
    body = (4, 12, 53, 52)
    terminal = (54, 23, 60, 41)
    shell_color = (235, 238, 245, 255)

    # Dark drop outline for crisp contrast against light taskbars
    offsets = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1))
    for dx, dy in offsets:
        draw.rounded_rectangle(
            (body[0] + dx, body[1] + dy, body[2] + dx, body[3] + dy),
            radius=7,
            outline=(15, 15, 20, 160),
            width=4,
        )
        draw.rounded_rectangle(
            (terminal[0] + dx, terminal[1] + dy, terminal[2] + dx, terminal[3] + dy),
            radius=3,
            fill=(15, 15, 20, 160),
        )

    # Battery shell
    draw.rounded_rectangle(body, radius=7, outline=shell_color, width=3)
    draw.rounded_rectangle(terminal, radius=3, fill=shell_color)

    # If exact percentage is requested, draw the bold number inside
    if percentage is not None:
        label = str(percentage)
        font = _font_for(label)
        bbox = draw.textbbox((0, 0), label, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = 28 - (w / 2) - bbox[0]
        y = 32 - (h / 2) - bbox[1]

        # Subtle dark halo under text for maximum legibility
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            draw.text((x + dx, y + dy), label, font=font, fill=(10, 10, 15, 180))
        draw.text((x, y), label, font=font, fill=color)
        return

    # Otherwise draw the 3 large capacity segment blocks
    segments = _LEVEL_SEGMENTS[level]

    if level is BatteryLevel.UNKNOWN:
        font = _cached_font(26)
        bbox = draw.textbbox((0, 0), "?", font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = 28 - (w / 2) - bbox[0]
        y = 32 - (h / 2) - bbox[1]
        draw.text((x, y), "?", font=font, fill=color)
        return

    segment_boxes = (
        (10, 18, 20, 46),
        (23, 18, 33, 46),
        (36, 18, 46, 46),
    )

    inactive = (50, 55, 65, 180)

    for index, box in enumerate(segment_boxes):
        fill = color if index < segments else inactive
        draw.rounded_rectangle(box, radius=3, fill=fill)


def _draw_charge_symbol(draw: ImageDraw.ImageDraw) -> None:
    """Overlay a compact lightning symbol."""
    bolt = (
        (32, 8),
        (24, 28),
        (30, 28),
        (25, 52),
        (40, 24),
        (34, 24),
    )
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        draw.polygon([(bx + dx, by + dy) for bx, by in bolt], fill=(10, 10, 15, 200))
    draw.polygon(bolt, fill=(255, 255, 255, 255))


def _draw_disconnected(draw: ImageDraw.ImageDraw) -> None:
    """Draw a neutral disconnected battery with diagonal cross."""
    body = (4, 12, 53, 52)
    terminal = (54, 23, 60, 41)
    draw.rounded_rectangle(body, radius=7, outline=(120, 125, 135, 200), width=3)
    draw.rounded_rectangle(terminal, radius=3, fill=(120, 125, 135, 200))
    draw.line((14, 20, 43, 44), fill=(140, 145, 155, 255), width=4)
    draw.line((43, 20, 14, 44), fill=(140, 145, 155, 255), width=4)


def _font_for(label: str) -> ImageFont.ImageFont:
    size = 20 if len(label) >= 3 else 28
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
