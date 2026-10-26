"""Hex / hue / lightness helpers and the shade-map coordinate system.

Map axes: hue runs red (left, 0 deg) -> yellow (right, 60 deg);
lightness runs white (top) -> black (bottom).
"""

import colorsys
import re

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

HUE_SPAN_DEGREES = 60.0


def is_valid_hex(value: str) -> bool:
    return bool(_HEX_RE.match(value))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    if not is_valid_hex(value):
        raise ValueError(f"Invalid hex color: {value!r}")
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


def hex_to_hue_lightness(value: str) -> tuple[float, float]:
    """Return (hue in degrees 0-360, lightness in percent 0-100)."""
    r, g, b = hex_to_rgb(value)
    hue, lightness, _ = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return round(hue * 360, 1), round(lightness * 100, 1)


def map_position(hue: float, lightness: float) -> tuple[float, float]:
    """Normalized (x, y) in [0, 1]; (0, 0) is the top-left of the map."""
    if hue >= 300:  # magenta-reds wrap around to the red edge
        hue -= 360
    x = min(max(hue / HUE_SPAN_DEGREES, 0.0), 1.0)
    y = min(max(1 - lightness / 100, 0.0), 1.0)
    return round(x, 4), round(y, 4)
