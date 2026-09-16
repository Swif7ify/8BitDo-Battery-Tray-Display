from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ICON_SIZE = 64


@lru_cache(maxsize=16)
def make_icon(label: str) -> Image.Image:
    """Create a small high-contrast tray icon showing the battery value."""
    image = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # A dark rounded tile stays legible on both light and dark taskbars.
    draw.rounded_rectangle((2, 2, 61, 61), radius=13, fill=(25, 25, 28, 255))
    draw.rounded_rectangle((2, 2, 61, 61), radius=13, outline=(225, 225, 225, 255), width=2)

    font = _font_for(label)
    bbox = draw.textbbox((0, 0), label, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = (ICON_SIZE - width) / 2
    y = (ICON_SIZE - height) / 2 - bbox[1]
    draw.text((x, y), label, font=font, fill=(255, 255, 255, 255))
    return image


def _font_for(label: str) -> ImageFont.ImageFont:
    size = 25 if len(label) >= 3 else 31
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
