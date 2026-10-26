"""Internal domain objects passed between services (not serialized to clients)."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AmazonShade:
    asin: str
    name: str
    swatch_url: str | None


@dataclass(frozen=True)
class AmazonProduct:
    """A retailer product; `asin` is the retailer's own product id (the name is historical)."""

    asin: str
    title: str
    brand: str | None
    detail_page_url: str | None
    image_url: str | None
    shades: tuple[AmazonShade, ...] = ()
    retailer: str = "amazon"


@dataclass(frozen=True)
class SearchOutcome:
    products: list[AmazonProduct]
    warnings: list[str]


@dataclass(frozen=True)
class FetchedImage:
    data: bytes
    content_type: str


@dataclass(frozen=True)
class ShadeExtraction:
    status: Literal["extracted", "failed"]
    hex: str | None = None
    hue: float | None = None
    lightness: float | None = None
    swatch_blob_name: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class CollectedShade:
    shade: AmazonShade
    extraction: ShadeExtraction


@dataclass(frozen=True)
class CollectedProduct:
    product: AmazonProduct
    shades: tuple[CollectedShade, ...]


@dataclass(frozen=True)
class MapShade:
    """A shade with an extracted hex, ready to be plotted."""

    shade_id: str
    product_id: str
    shade_name: str
    product_title: str
    hex: str
    hue: float
    lightness: float


@dataclass(frozen=True)
class PlottedMarker:
    shade: MapShade
    x: float
    y: float


@dataclass(frozen=True)
class ColorMapRecord:
    id: str
    blob_name: str
    width: int
    height: int
    markers: tuple[PlottedMarker, ...]
