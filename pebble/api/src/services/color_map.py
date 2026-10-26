"""Renders the shade color map image and computes each shade's marker position."""

import colorsys
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from src.models.domain import MapShade, PlottedMarker
from src.services.color_math import HUE_SPAN_DEGREES, hex_to_rgb, map_position

_GRADIENT_SIZE = (120, 80)
_MARKER_RADIUS = 9
_MARGIN = 14


def _background(width: int, height: int) -> Image.Image:
    gw, gh = _GRADIENT_SIZE
    gradient = Image.new("RGB", (gw, gh))
    pixels = gradient.load()
    for gx in range(gw):
        hue = (gx / (gw - 1)) * HUE_SPAN_DEGREES / 360
        for gy in range(gh):
            lightness = 1 - gy / (gh - 1)
            r, g, b = colorsys.hls_to_rgb(hue, lightness, 1.0)
            pixels[gx, gy] = (round(r * 255), round(g * 255), round(b * 255))
    return gradient.resize((width, height), Image.Resampling.BICUBIC)


def _label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font) -> None:  # noqa: ANN001
    left, top, right, bottom = draw.textbbox(xy, text, font=font)
    draw.rectangle((left - 4, top - 2, right + 4, bottom + 2), fill=(255, 255, 255, 200))
    draw.text(xy, text, fill=(43, 35, 33), font=font)


class ColorMapRenderer:
    def __init__(self, width: int = 900, height: int = 600) -> None:
        self.width = width
        self.height = height

    def plot(self, shades: list[MapShade]) -> list[PlottedMarker]:
        return [PlottedMarker(s, *map_position(s.hue, s.lightness)) for s in shades]

    def render(self, markers: list[PlottedMarker]) -> bytes:
        image = _background(self.width, self.height).convert("RGBA")
        draw = ImageDraw.Draw(image, "RGBA")
        font = ImageFont.load_default()

        _label(draw, (_MARGIN, self.height // 2 - 6), "Red", font)
        _label(draw, (self.width - 64, self.height // 2 - 6), "Yellow", font)
        _label(draw, (self.width // 2 - 14, _MARGIN), "White", font)
        _label(draw, (_MARGIN, self.height - 26), "Black", font)

        for marker in markers:
            cx = round(marker.x * (self.width - 1))
            cy = round(marker.y * (self.height - 1))
            box = (
                cx - _MARKER_RADIUS,
                cy - _MARKER_RADIUS,
                cx + _MARKER_RADIUS,
                cy + _MARKER_RADIUS,
            )
            draw.ellipse(
                box,
                fill=(*hex_to_rgb(marker.shade.hex), 255),
                outline=(255, 255, 255, 255),
                width=3,
            )
            draw.ellipse(
                (box[0] - 1, box[1] - 1, box[2] + 1, box[3] + 1),
                outline=(43, 35, 33, 255),
                width=1,
            )

        buffer = BytesIO()
        image.convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()
