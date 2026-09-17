from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .model import BatteryLevel

ICON_SIZE = 256

_LEVEL_COLORS: dict[BatteryLevel, tuple[int, int, int, int]] = {
    BatteryLevel.EMPTY: (255, 60, 60, 255),
    BatteryLevel.LOW: (255, 130, 35, 255),
    BatteryLevel.MEDIUM: (255, 210, 45, 255),
    BatteryLevel.FULL: (50, 245, 110, 255),
    BatteryLevel.UNKNOWN: (160, 165, 175, 255),
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
        color = (60, 215, 255, 255)  # Electric Cyan
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
    """Draw the battery shell wider in width, preserving height, across canvas."""
    body = (1, 32, 238, 224)
    terminal = (238, 86, 255, 170)
    rad = 34
    stroke = 14

    shell_color = (
        color
        if (level == BatteryLevel.EMPTY and percentage is None)
        else (245, 248, 255, 255)
    )

    # Multi-directional dark drop outline for contrast on light/dark taskbars
    offsets = (
        (-2, 0), (2, 0), (0, -2), (0, 2),
        (-2, -2), (2, 2), (-2, 2), (2, -2),
    )
    for dx, dy in offsets:
        draw.rounded_rectangle(
            (body[0] + dx, body[1] + dy, body[2] + dx, body[3] + dy),
            radius=rad,
            outline=(10, 10, 15, 240),
            width=stroke + 4,
        )
        draw.rounded_rectangle(
            (terminal[0] + dx, terminal[1] + dy, terminal[2] + dx, terminal[3] + dy),
            radius=12,
            fill=(10, 10, 15, 240),
        )

    # Battery shell
    draw.rounded_rectangle(body, radius=rad, outline=shell_color, width=stroke)
    draw.rounded_rectangle(terminal, radius=12, fill=shell_color)

    # If exact percentage is requested, draw bold thick number inside
    if percentage is not None:
        label = str(percentage)
        font = _font_for(label)
        bbox = draw.textbbox((0, 0), label, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        cx = (body[0] + body[2]) / 2
        cy = (body[1] + body[3]) / 2
        x = cx - (w / 2) - bbox[0]
        y = cy - (h / 2) - bbox[1]

        # Crisp stroke outline for maximum visibility without eating into glyph
        draw.text(
            (x, y),
            label,
            font=font,
            fill=color,
            stroke_width=2,
            stroke_fill=(10, 10, 15, 240),
        )
        return

    # Otherwise draw 3 capacity blocks
    segments = _LEVEL_SEGMENTS[level]

    if level is BatteryLevel.UNKNOWN:
        font = _cached_font(110)
        bbox = draw.textbbox((0, 0), "?", font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        cx = (body[0] + body[2]) / 2
        cy = (body[1] + body[3]) / 2
        x = cx - (w / 2) - bbox[0]
        y = cy - (h / 2) - bbox[1]
        draw.text(
            (x, y),
            "?",
            font=font,
            fill=color,
            stroke_width=2,
            stroke_fill=(10, 10, 15, 240),
        )
        return

    pad_x = stroke + 10
    pad_y = stroke + 10
    ix0 = body[0] + pad_x
    ix1 = body[2] - pad_x
    iy0 = body[1] + pad_y
    iy1 = body[3] - pad_y
    avail_w = ix1 - ix0
    seg_gap = 10
    sw = (avail_w - (2 * seg_gap)) // 3
    inactive = (50, 55, 65, 180)

    for i in range(3):
        bx0 = ix0 + i * (sw + seg_gap)
        bx1 = bx0 + sw
        f = color if i < segments else inactive
        draw.rounded_rectangle((bx0, iy0, bx1, iy1), radius=12, fill=f)


def _draw_charge_symbol(draw: ImageDraw.ImageDraw) -> None:
    """Overlay an electric lightning symbol centered over the battery."""
    cx = 120
    cy = 128
    y0 = 32
    y1 = 224
    bolt = (
        (cx + 8, y0 + 12),
        (cx - 36, cy + 2),
        (cx - 4, cy + 2),
        (cx - 24, y1 - 10),
        (cx + 40, cy - 8),
        (cx + 10, cy - 8),
    )
    for dx in (-2, 0, 2):
        for dy in (-2, 0, 2):
            if dx or dy:
                draw.polygon([(bx + dx, by + dy) for bx, by in bolt], fill=(10, 10, 15, 240))
    draw.polygon(bolt, fill=(60, 215, 255, 255))


def _draw_disconnected(draw: ImageDraw.ImageDraw) -> None:
    """Draw a neutral disconnected battery with diagonal cross."""
    body = (1, 32, 238, 224)
    terminal = (238, 86, 255, 170)
    rad = 34
    stroke = 14
    draw.rounded_rectangle(body, radius=rad, outline=(120, 125, 135, 200), width=stroke)
    draw.rounded_rectangle(terminal, radius=12, fill=(120, 125, 135, 200))
    pad = stroke + 24
    draw.line(
        (body[0] + pad, body[1] + pad, body[2] - pad, body[3] - pad),
        fill=(140, 145, 155, 255),
        width=int(stroke * 1.2),
    )
    draw.line(
        (body[2] - pad, body[1] + pad, body[0] + pad, body[3] - pad),
        fill=(140, 145, 155, 255),
        width=int(stroke * 1.2),
    )


def _font_for(label: str) -> ImageFont.ImageFont:
    # Size 100 for 3 digits (100), size 142 for 1-2 digits (88)
    size = 100 if len(label) >= 3 else 142
    return _cached_font(size)


@lru_cache(maxsize=8)
def _cached_font(size: int) -> ImageFont.ImageFont:
    windows_dir = Path(os.environ.get("WINDIR", r"C:\Windows"))
    candidates = (
        windows_dir / "Fonts" / "ariblk.ttf",
        windows_dir / "Fonts" / "impact.ttf",
        windows_dir / "Fonts" / "arialbd.ttf",
        windows_dir / "Fonts" / "segoeuib.ttf",
    )
    for path in candidates:
        try:
            return ImageFont.truetype(str(path), size=size)
        except OSError:
            continue
    return ImageFont.load_default()
