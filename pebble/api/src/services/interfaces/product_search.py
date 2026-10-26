from collections.abc import Sequence
from typing import Protocol

from src.models.domain import AmazonProduct, SearchOutcome


class ProductSearch(Protocol):
    """One retailer: finds foundation products and expands each one into its shade variations."""

    def search(self, query: str, max_products: int) -> list[AmazonProduct]: ...

    def health_check(self) -> bool: ...


class CatalogSearch(Protocol):
    """Searches the selected retailers; a failing retailer becomes a warning, not an error."""

    def search(
        self, query: str, max_products: int, retailers: Sequence[str] = ("amazon",)
    ) -> SearchOutcome: ...

    def health_check(self) -> bool: ...
