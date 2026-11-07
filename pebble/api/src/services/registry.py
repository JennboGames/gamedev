"""Composition root. The only place that reads the environment and picks implementations."""

from dataclasses import dataclass
from pathlib import Path

from src.models.api import Product
from src.services.blob_providers import create_blob_client_provider
from src.services.blob_store import AzureBlobStore
from src.services.catalog import CATALOG_RETAILER, CatalogImporter, matches_query
from src.services.collector import ColorMapService, FoundationCollector
from src.services.color_extractor import PillowColorExtractor
from src.services.color_map import ColorMapRenderer
from src.services.config import DEFAULT_CATALOG_PATH, load_config
from src.services.image_fetcher import HttpImageFetcher
from src.services.interfaces.blob_store import BlobStore
from src.services.interfaces.color_extractor import ColorExtractor
from src.services.interfaces.image_fetcher import ImageFetcher
from src.services.interfaces.product_search import CatalogSearch
from src.services.interfaces.shade_repository import ShadeRepository
from src.services.postgres_providers import create_connection_provider
from src.services.postgres_repository import PostgresShadeRepository
from src.services.retailer_search import MultiRetailerSearch


@dataclass
class ServiceRegistry:
    repository: ShadeRepository
    blob_store: BlobStore
    product_search: CatalogSearch
    image_fetcher: ImageFetcher
    color_extractor: ColorExtractor
    extraction_workers: int = 8
    catalog_path: Path = DEFAULT_CATALOG_PATH
    # Limits the color map to one product source; None plots every source.
    color_map_retailer: str | None = None

    def catalog_importer(self) -> CatalogImporter:
        return CatalogImporter(self.repository, self.catalog_path)

    def catalog_products(self) -> list[Product]:
        """Products from catalog/products.json only; imports the file when none are stored yet."""
        products = [p for p in self.repository.list_products() if p.retailer == CATALOG_RETAILER]
        if products:
            return products
        _, imported = self.catalog_importer().import_catalog()
        return imported

    def search_catalog(self, query: str, max_products: int) -> tuple[list[Product], list[str]]:
        matches = [p for p in self.catalog_products() if matches_query(p, query)]
        warnings = [] if matches else [f'No catalog products match "{query}".']
        return matches[:max_products], warnings

    def prepare_color_map_source(self) -> None:
        """When the map is limited to the catalog, make sure the catalog is stored first."""
        if self.color_map_retailer == CATALOG_RETAILER:
            self.catalog_products()

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
        return ColorMapService(
            self.repository, self.blob_store, ColorMapRenderer(), self.color_map_retailer
        )


_services: ServiceRegistry | None = None


def initialize_services() -> ServiceRegistry:
    """Pick Azurite/local PostgreSQL only for explicit Development; otherwise managed identity."""
    global _services
    config = load_config()
    _services = ServiceRegistry(
        repository=PostgresShadeRepository(create_connection_provider(config)),
        blob_store=AzureBlobStore(create_blob_client_provider(config)),
        # Every product comes from catalog/products.json; no retailer is contacted.
        product_search=MultiRetailerSearch({}),
        image_fetcher=HttpImageFetcher(),
        color_extractor=PillowColorExtractor(),
        extraction_workers=config.extraction_workers,
        catalog_path=config.catalog_path,
        color_map_retailer=CATALOG_RETAILER,
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
