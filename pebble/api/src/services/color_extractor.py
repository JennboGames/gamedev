"""Swatch image -> dominant hex, using Pillow."""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

from src.services.color_math import rgb_to_hex

_NEAR_WHITE = 240
_MIN_ALPHA = 128
_SAMPLE_SIZE = (64, 64)


def _median(values: list[int]) -> int:
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def _pixels(image: Image.Image) -> list[tuple[int, ...]]:
    # getdata() is deprecated from Pillow 13 in favour of get_flattened_data().
    flatten = getattr(image, "get_flattened_data", image.getdata)
    return list(flatten())


class PillowColorExtractor:
    """Median color of the swatch's central region, ignoring transparent and near-white pixels."""

    def extract_hex(self, image_bytes: bytes) -> str:
        try:
            with Image.open(BytesIO(image_bytes)) as source:
                image = source.convert("RGBA")
        except (UnidentifiedImageError, OSError) as exc:
            raise ValueError("The swatch is not a readable image") from exc

        image.thumbnail(_SAMPLE_SIZE)
        width, height = image.size
        center = image.crop((width // 4, height // 4, width - width // 4, height - height // 4))

        opaque = [p for p in _pixels(center) if p[3] >= _MIN_ALPHA]
        colored = [p for p in opaque if min(p[0], p[1], p[2]) < _NEAR_WHITE]
        pixels = colored or opaque
        if not pixels:
            pixels = [p for p in _pixels(image) if p[3] >= _MIN_ALPHA]
        if not pixels:
            raise ValueError("The swatch has no visible pixels")

        return rgb_to_hex(
            _median([p[0] for p in pixels]),
            _median([p[1] for p in pixels]),
            _median([p[2] for p in pixels]),
        )
