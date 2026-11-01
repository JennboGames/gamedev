"""Renders the full color wheel and computes each shade's marker position on it.

Hue is the angle (red at the top, clockwise); lightness is the distance from the center
(white in the middle, black on the rim).
"""

import colorsys
import math
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from src.models.domain import MapShade, PlottedMarker
from src.services.color_map import draw_markers
from src.services.color_math import WHEEL_RADIUS, wheel_position

_GRADIENT_SIZE = 240
_SUPERSAMPLE = 4
_SURFACE = (250, 246, 242)
_HUE_LABELS = (
    ("Red", 0),
    ("Yellow", 60),
    ("Green", 120),
    ("Cyan", 180),
    ("Blue", 240),
    ("Magenta", 300),
)


def _wheel_gradient() -> Image.Image:
    size = _GRADIENT_SIZE
    gradient = Image.new("RGB", (size, size))
    pixels = gradient.load()
    for gx in range(size):
        u = (gx + 0.5) / size * 2 - 1
        for gy in range(size):
            v = (gy + 0.5) / size * 2 - 1
            hue = (math.degrees(math.atan2(u, -v)) % 360) / 360
            # Pixels beyond the rim stay black so the resize never bleeds color into the edge.
            lightness = max(0.0, 1 - math.hypot(u, v) / 2 / WHEEL_RADIUS)
            r, g, b = colorsys.hls_to_rgb(hue, lightness, 1.0)
            pixels[gx, gy] = (round(r * 255), round(g * 255), round(b * 255))
    return gradient


def _rim_mask(size: int) -> Image.Image:
    big = size * _SUPERSAMPLE
    mask = Image.new("L", (big, big), 0)
    radius = WHEEL_RADIUS * big
    center = big / 2
    ImageDraw.Draw(mask).ellipse(
        (center - radius, center - radius, center + radius, center + radius), fill=255
    )
    return mask.resize((size, size), Image.Resampling.LANCZOS)


class ColorWheelRenderer:
    def __init__(self, size: int = 720) -> None:
        self.width = size
        self.height = size

    def plot(self, shades: list[MapShade]) -> list[PlottedMarker]:
        return [PlottedMarker(s, *wheel_position(s.hue, s.lightness)) for s in shades]

    def render_background(self) -> bytes:
        """The wheel and hue labels without markers; the web app overlays markers so they stay crisp."""
        return self.render([])

    def render(self, markers: list[PlottedMarker]) -> bytes:
        """The complete image, with hue labels and markers (for download)."""
        size = self.width
        wheel = _wheel_gradient().resize((size, size), Image.Resampling.BICUBIC)
        image = Image.composite(wheel, Image.new("RGB", (size, size), _SURFACE), _rim_mask(size))
        image = image.convert("RGBA")
        draw = ImageDraw.Draw(image, "RGBA")
        font = ImageFont.load_default()

        label_radius = (WHEEL_RADIUS + 0.5) / 2
        for text, hue in _HUE_LABELS:
            angle = math.radians(hue)
            cx = size * (0.5 + label_radius * math.sin(angle))
            cy = size * (0.5 - label_radius * math.cos(angle))
            left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
            xy = (cx - (right - left) / 2, cy - (bottom - top) / 2)
            draw.text(xy, text, fill=(43, 35, 33), font=font)

        draw_markers(draw, markers, self.width, self.height)

        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()
