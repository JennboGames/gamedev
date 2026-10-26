from typing import Protocol

from src.models.api import Product, Shade
from src.models.domain import CollectedProduct, ColorMapRecord, MapShade, ShadeExtraction


class ShadeRepository(Protocol):
    """Persistence for products, shades, and generated color maps."""

    def save_search(
        self, query: str, products: list[CollectedProduct]
    ) -> tuple[str, list[Product]]:
        """Atomically store a search with its products and shades. Returns (search_id, products)."""
        ...

    def list_products(self) -> list[Product]: ...

    def get_product(self, product_id: str) -> Product | None: ...

    def list_shades(self, product_id: str) -> list[Shade]: ...

    def get_shade(self, shade_id: str) -> Shade | None: ...

    def update_shade_extraction(self, shade_id: str, extraction: ShadeExtraction) -> Shade | None:
        """Update one shade and refresh its product status in one transaction."""
        ...

    def list_map_shades(self, product_ids: list[str] | None) -> list[MapShade]:
        """Shades that have an extracted hex, optionally limited to some products."""
        ...

    def save_color_map(self, record: ColorMapRecord) -> None:
        """Atomically store a color map and all of its markers."""
        ...

    def get_latest_color_map(self) -> ColorMapRecord | None: ...

    def health_check(self) -> bool: ...
