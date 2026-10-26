"""Composition root. The only place that reads the environment and picks implementations."""

from dataclasses import dataclass

from src.services.amazon_paapi import AmazonPaapiClient
from src.services.blob_providers import create_blob_client_provider
from src.services.blob_store import AzureBlobStore
from src.services.collector import ColorMapService, FoundationCollector
from src.services.color_extractor import PillowColorExtractor
from src.services.color_map import ColorMapRenderer
from src.services.config import load_config
from src.services.image_fetcher import HttpImageFetcher
from src.services.interfaces.blob_store import BlobStore
from src.services.interfaces.color_extractor import ColorExtractor
from src.services.interfaces.image_fetcher import ImageFetcher
from src.services.interfaces.product_search import CatalogSearch
from src.services.interfaces.shade_repository import ShadeRepository
from src.services.postgres_providers import create_connection_provider
from src.services.postgres_repository import PostgresShadeRepository
from src.services.retailer_search import MultiRetailerSearch, UnavailableSearch
from src.services.ulta_search import UltaSearch

SEPHORA_UNAVAILABLE = (
    "Sephora blocks automated access (HTTP 403), so its products cannot be collected."
)


@dataclass
class ServiceRegistry:
    repository: ShadeRepository
    blob_store: BlobStore
    product_search: CatalogSearch
    image_fetcher: ImageFetcher
    color_extractor: ColorExtractor
    extraction_workers: int = 8

    def collector(self) -> FoundationCollector:
        return FoundationCollector(
            self.product_search,
            self.image_fetcher,
            self.color_extractor,
            self.blob_store,
            self.repository,
            workers=self.extraction_workers,
        )

    def color_maps(self) -> ColorMapService:
        return ColorMapService(self.repository, self.blob_store, ColorMapRenderer())


_services: ServiceRegistry | None = None


def initialize_services() -> ServiceRegistry:
    """Pick Azurite/local PostgreSQL only for explicit Development; otherwise managed identity."""
    global _services
    config = load_config()
    amazon = AmazonPaapiClient(config)
    _services = ServiceRegistry(
        repository=PostgresShadeRepository(create_connection_provider(config)),
        blob_store=AzureBlobStore(create_blob_client_provider(config)),
        product_search=MultiRetailerSearch(
            {
                "amazon": amazon,
                "ulta": UltaSearch(max_shades=config.max_shades_per_product),
                "sephora": UnavailableSearch(SEPHORA_UNAVAILABLE),
            },
            pinned=amazon.pinned_products,
        ),
        image_fetcher=HttpImageFetcher(),
        color_extractor=PillowColorExtractor(),
        extraction_workers=config.extraction_workers,
    )
    return _services


def register_services(registry: ServiceRegistry) -> None:
    global _services
    _services = registry


def get_services() -> ServiceRegistry:
    if _services is None:
        return initialize_services()
    return _services


def clear_services() -> None:
    global _services
    _services = None
