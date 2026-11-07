"""Fans a search out to the selected retailers and merges the results."""

from collections.abc import Callable, Mapping, Sequence

from src.errors.error_types import AppError, ConfigurationError, UpstreamError
from src.logger import get_logger
from src.models.domain import SearchOutcome, SourceProduct
from src.services.interfaces.product_search import ProductSearch

logger = get_logger("retailer_search")

RETAILER_LABELS = {"ulta": "Ulta", "sephora": "Sephora"}


class UnavailableSearch:
    """A retailer that is listed but cannot be searched; every search reports why."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    def search(self, query: str, max_products: int) -> list[SourceProduct]:
        raise UpstreamError(self._reason)

    def health_check(self) -> bool:
        return False


class MultiRetailerSearch:
    def __init__(self, providers: Mapping[str, ProductSearch]) -> None:
        self._providers = providers

    def search(
        self, query: str, max_products: int, retailers: Sequence[str] = ()
    ) -> SearchOutcome:
        products: list[SourceProduct] = []
        warnings: list[str] = []
        errors: list[AppError] = []
        seen: set[tuple[str, str]] = set()

        def add(found: list[SourceProduct]) -> None:
            for product in found:
                key = (product.retailer, product.asin)
                if key not in seen:
                    seen.add(key)
                    products.append(product)

        selected = list(dict.fromkeys(retailers))

        for retailer in selected:
            label = RETAILER_LABELS.get(retailer, retailer)
            provider = self._providers.get(retailer)
            if provider is None:
                warnings.append(f"{label} search is not available.")
                continue
            self._attempt(
                label, lambda p=provider: p.search(query, max_products), add, warnings, errors
            )

        if not products and errors and len(errors) == len(selected):
            raise errors[0]
        return SearchOutcome(products=products, warnings=warnings)

    @staticmethod
    def _attempt(
        label: str,
        fetch: Callable[[], list[SourceProduct]],
        add: Callable[[list[SourceProduct]], None],
        warnings: list[str],
        errors: list[AppError],
    ) -> None:
        try:
            add(fetch())
        except (UpstreamError, ConfigurationError) as exc:
            logger.warning("retailer_failed", retailer=label, error=exc.message)
            warnings.append(f"{label}: {exc.message}")
            errors.append(exc)

    def health_check(self) -> bool:
        return bool(self._providers) and all(p.health_check() for p in self._providers.values())
