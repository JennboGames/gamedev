"""Use-case orchestration: collecting foundations and generating the shade color map."""

import uuid
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor

from src.errors.error_types import NotFoundError, UpstreamError
from src.logger import get_logger
from src.models.api import ColorMap, Marker, Product, Shade
from src.models.domain import (
    AmazonShade,
    CollectedProduct,
    CollectedShade,
    ColorMapRecord,
    ShadeExtraction,
)
from src.services.color_map import ColorMapRenderer
from src.services.color_math import hex_to_hue_lightness
from src.services.interfaces.blob_store import BlobStore
from src.services.interfaces.color_extractor import ColorExtractor
from src.services.interfaces.image_fetcher import ImageFetcher
from src.services.interfaces.product_search import CatalogSearch
from src.services.interfaces.shade_repository import ShadeRepository

logger = get_logger("collector")

SWATCH_CONTAINER = "swatches"
COLORMAP_CONTAINER = "colormaps"

_EXTENSIONS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


class FoundationCollector:
    def __init__(
        self,
        product_search: CatalogSearch,
        image_fetcher: ImageFetcher,
        color_extractor: ColorExtractor,
        blob_store: BlobStore,
        repository: ShadeRepository,
        workers: int = 8,
    ) -> None:
        self._product_search = product_search
        self._image_fetcher = image_fetcher
        self._color_extractor = color_extractor
        self._blob_store = blob_store
        self._repository = repository
        self._workers = workers

    def collect(
        self, query: str, max_products: int, retailers: Sequence[str] = ("amazon",)
    ) -> tuple[str, list[Product], list[str]]:
        outcome = self._product_search.search(query, max_products, retailers)
        collected: list[CollectedProduct] = []
        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            for product in outcome.products:
                extractions = list(
                    pool.map(
                        lambda s, p=product: self._extract(p.retailer, p.asin, s), product.shades
                    )
                )
                collected.append(
                    CollectedProduct(
                        product=product,
                        shades=tuple(
                            CollectedShade(s, e) for s, e in zip(product.shades, extractions)
                        ),
                    )
                )
        logger.info("search_collected", query=query, products=len(collected))
        search_id, saved = self._repository.save_search(query, collected)
        return search_id, saved, outcome.warnings

    def reextract_shade(self, shade_id: str) -> Shade:
        shade = self._repository.get_shade(shade_id)
        if shade is None:
            raise NotFoundError("Shade", shade_id)
        product = self._repository.get_product(str(shade.product_id))
        if product is None:
            raise NotFoundError("Product", str(shade.product_id))

        extraction = self._extract(
            product.retailer,
            product.asin,
            AmazonShade(asin=shade.asin, name=shade.name, swatch_url=shade.swatch_url),
        )
        if extraction.status == "failed":
            # Keep a previously extracted hex; only record the failure when there is nothing to keep.
            if shade.hex is None:
                self._repository.update_shade_extraction(shade_id, extraction)
            raise UpstreamError(extraction.error or "The swatch could not be processed")

        updated = self._repository.update_shade_extraction(shade_id, extraction)
        if updated is None:
            raise NotFoundError("Shade", shade_id)
        return updated

    def _extract(self, retailer: str, product_asin: str, shade: AmazonShade) -> ShadeExtraction:
        """Fetch and analyze one swatch. Per-shade problems are recorded, never raised."""
        if not shade.swatch_url:
            return ShadeExtraction(status="failed", error="This shade has no swatch image")
        try:
            image = self._image_fetcher.fetch(shade.swatch_url)
            hex_color = self._color_extractor.extract_hex(image.data)
        except (UpstreamError, ValueError) as exc:
            logger.warning("swatch_failed", shade=shade.asin, reason=str(exc))
            return ShadeExtraction(status="failed", error=str(exc))

        blob_name = (
            f"{retailer}/{product_asin}/{shade.asin}.{_EXTENSIONS.get(image.content_type, 'img')}"
        )
        self._blob_store.upload(SWATCH_CONTAINER, blob_name, image.data, image.content_type)
        hue, lightness = hex_to_hue_lightness(hex_color)
        return ShadeExtraction(
            status="extracted",
            hex=hex_color,
            hue=hue,
            lightness=lightness,
            swatch_blob_name=blob_name,
        )


class ColorMapService:
    def __init__(
        self, repository: ShadeRepository, blob_store: BlobStore, renderer: ColorMapRenderer
    ) -> None:
        self._repository = repository
        self._blob_store = blob_store
        self._renderer = renderer

    def generate(self, product_ids: list[str] | None) -> ColorMap:
        shades = self._repository.list_map_shades(product_ids)
        if not shades:
            raise NotFoundError("Shades with an extracted hex color")

        markers = self._renderer.plot(shades)
        png = self._renderer.render(markers)
        record = ColorMapRecord(
            id=str(uuid.uuid4()),
            blob_name=f"{uuid.uuid4()}.png",
            width=self._renderer.width,
            height=self._renderer.height,
            markers=tuple(markers),
        )
        self._blob_store.upload(COLORMAP_CONTAINER, record.blob_name, png, "image/png")
        self._repository.save_color_map(record)
        return self._to_api(record)

    def latest(self) -> ColorMap:
        record = self._repository.get_latest_color_map()
        if record is None:
            raise NotFoundError("Color map")
        return self._to_api(record)

    def _to_api(self, record: ColorMapRecord) -> ColorMap:
        return ColorMap(
            image_url=self._blob_store.read_url(COLORMAP_CONTAINER, record.blob_name),
            width=record.width,
            height=record.height,
            markers=[
                Marker(
                    shade_id=m.shade.shade_id,
                    product_id=m.shade.product_id,
                    shade_name=m.shade.shade_name,
                    product_title=m.shade.product_title,
                    hex=m.shade.hex,
                    hue=m.shade.hue,
                    lightness=m.shade.lightness,
                    x=m.x,
                    y=m.y,
                )
                for m in record.markers
            ],
        )
