from __future__ import annotations

from PIL import Image

from eightbitdo_battery_tray.icon_factory import ICON_SIZE, make_icon


def test_make_icon_dimensions_and_mode() -> None:
    img = make_icon("75")
    assert isinstance(img, Image.Image)
    assert img.size == (ICON_SIZE, ICON_SIZE)
    assert img.mode == "RGBA"


def test_make_icon_labels() -> None:
    for label in ("--", "0", "15", "50", "99", "100"):
        img = make_icon(label)
        assert img.size == (ICON_SIZE, ICON_SIZE)


def test_make_icon_integer_and_none() -> None:
    img_int = make_icon(88)
    assert img_int.size == (ICON_SIZE, ICON_SIZE)
    img_none = make_icon(None, connected=True)
    assert img_none.size == (ICON_SIZE, ICON_SIZE)
    img_disco = make_icon(None, connected=False)
    assert img_disco.size == (ICON_SIZE, ICON_SIZE)


def test_make_icon_charging_color() -> None:
    img_normal = make_icon("80", charging=False)
    img_charging = make_icon("80", charging=True)
    assert img_normal.tobytes() != img_charging.tobytes()


def test_make_icon_low_battery_color() -> None:
    img_low = make_icon("10", charging=False)
    img_nominal = make_icon("80", charging=False)
    assert img_low.tobytes() != img_nominal.tobytes()


def test_make_icon_disconnected_state() -> None:
    img_connected = make_icon(88, connected=True)
    img_disconnected = make_icon(88, connected=False)
    assert img_connected.tobytes() != img_disconnected.tobytes()
