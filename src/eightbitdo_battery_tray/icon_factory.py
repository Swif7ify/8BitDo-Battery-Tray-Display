from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

ICON_SIZE = 64

# Color Palette (Tailored for high contrast on light & dark Windows taskbars)
COLOR_CHARGING = (0, 215, 255, 255)       # Electric Cyan
COLOR_HIGH = (60, 220, 110, 255)          # Vivid Emerald Green (> 50%)
COLOR_MEDIUM = (250, 185, 45, 255)        # Amber / Warm Gold (21% - 50%)
COLOR_LOW = (240, 65, 65, 255)            # Alert Red (<= 20%)
COLOR_DISCONNECTED = (115, 120, 130, 255)  # Muted Slate Gray


@lru_cache(maxsize=128)
def make_icon(
    level: int | str | None = None,
    charging: bool = False,
    connected: bool = True,
) -> Image.Image:
    """Create a high-contrast 64x64 tray icon with the 8BitDo logo and a color battery checker."""
    # 1. Normalize level and connection status
    pct: int | None = None
    if isinstance(level, str):
        if level == "--":
            connected = False
        else:
            try:
                pct = int(level.rstrip("%"))
            except ValueError:
                pct = None
    elif isinstance(level, int):
        pct = max(0, min(100, level))

    if not connected:
        accent = COLOR_DISCONNECTED
        border_alpha = 60
        filled_segments = 0
    elif charging:
        accent = COLOR_CHARGING
        border_alpha = 220
        filled_segments = _segments_for(pct) if pct is not None else 4
    else:
        if pct is None:
            accent = COLOR_HIGH
            filled_segments = 4
        elif pct <= 20:
            accent = COLOR_LOW
            filled_segments = 1
        elif pct <= 50:
            accent = COLOR_MEDIUM
            filled_segments = 2
        elif pct <= 75:
            accent = COLOR_HIGH
            filled_segments = 3
        else:
            accent = COLOR_HIGH
            filled_segments = 4
        border_alpha = 200

    # 2. Base tile: modern rounded dark slate card
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    tile_rect = (2, 2, 61, 61)
    draw.rounded_rectangle(tile_rect, radius=12, fill=(22, 22, 26, 255))
    draw.rounded_rectangle(
        tile_rect,
        radius=12,
        outline=(accent[0], accent[1], accent[2], border_alpha),
        width=2,
    )

    # 3. 8BitDo Logo in the top half
    logo = _load_logo()
    if logo is not None:
        logo_w = 48
        logo_h = int(logo_w * (logo.height / logo.width))
        logo_resized = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        if not connected:
            r, g, b, a = logo_resized.split()
            a = a.point(lambda p: int(p * 0.35))
            logo_resized = Image.merge("RGBA", (r, g, b, a))
        logo_x = (ICON_SIZE - logo_w) // 2
        logo_y = 12
        image.paste(logo_resized, (logo_x, logo_y), logo_resized)
    else:
        # Fallback: draw retro controller silhouette
        _draw_controller_fallback(draw, connected=connected)

    # 4. Battery Checker Color Indicator in the bottom half
    checker_y = 35
    checker_h = 16

    if not connected:
        # Offline muted slot with centered dot
        bar_rect = (10, checker_y, 53, checker_y + checker_h)
        draw.rounded_rectangle(bar_rect, radius=8, fill=(35, 36, 42, 255))
        draw.rounded_rectangle(bar_rect, radius=8, outline=(80, 85, 95, 255), width=2)
        draw.ellipse((30, checker_y + 6, 34, checker_y + 10), fill=(100, 105, 115, 255))
    else:
        bar_rect = (8, checker_y, 55, checker_y + checker_h)
        draw.rounded_rectangle(bar_rect, radius=8, fill=(30, 32, 38, 255))
        bar_outline = (accent[0], accent[1], accent[2], 120)
        draw.rounded_rectangle(bar_rect, radius=8, outline=bar_outline, width=1)

        seg_w = 9
        seg_h = 10
        seg_y = checker_y + 3
        start_x = 11

        for i in range(4):
            sx = start_x + i * 11
            box = (sx, seg_y, sx + seg_w, seg_y + seg_h)
            if i < filled_segments:
                draw.rounded_rectangle(box, radius=3, fill=accent)
            else:
                draw.rounded_rectangle(box, radius=3, fill=(45, 48, 56, 255))

        if charging:
            # Electric lightning bolt overlay
            bolt = [
                (33, checker_y - 3),
                (29, checker_y + 8),
                (33, checker_y + 8),
                (31, checker_y + 19),
                (36, checker_y + 7),
                (32, checker_y + 7),
            ]
            draw.polygon(bolt, fill=(255, 255, 255, 255))

    return image


def _segments_for(pct: int) -> int:
    if pct <= 20:
        return 1
    if pct <= 50:
        return 2
    if pct <= 75:
        return 3
    return 4


@lru_cache(maxsize=1)
def _load_logo() -> Image.Image | None:
    """Load the bundled 8BitDo high-res logo asset."""
    candidates = []
    if getattr(sys, "frozen", False):
        meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        candidates.extend([
            meipass / "eightbitdo_battery_tray" / "assets" / "8bitdo_logo_white.png",
            meipass / "assets" / "8bitdo_logo_white.png",
        ])

    assets_dir = Path(__file__).resolve().parent / "assets"
    candidates.append(assets_dir / "8bitdo_logo_white.png")

    for path in candidates:
        if path.is_file():
            try:
                return Image.open(path).convert("RGBA")
            except (OSError, ValueError):
                continue
    return None


def _draw_controller_fallback(draw: ImageDraw.ImageDraw, connected: bool) -> None:
    """Draw a minimalist retro gamepad silhouette when asset file is missing."""
    fill_color = (230, 230, 235, 255) if connected else (100, 105, 115, 255)
    # Controller body
    draw.rounded_rectangle((12, 10, 51, 26), radius=5, fill=fill_color)
    # Grips
    draw.ellipse((10, 14, 22, 28), fill=fill_color)
    draw.ellipse((41, 14, 53, 28), fill=fill_color)
