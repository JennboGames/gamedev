from typing import Protocol


class ColorExtractor(Protocol):
    """Turns a swatch image into a single `#RRGGBB` hex color."""

    def extract_hex(self, image_bytes: bytes) -> str: ...
