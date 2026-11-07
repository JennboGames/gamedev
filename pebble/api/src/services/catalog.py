"""Imports the curated shade catalog (catalog/products.json) as products and shades."""

import json
import re
import unicodedata
from pathlib import Path

from src.errors.error_types import ConfigurationError, ValidationError
from src.logger import get_logger
from src.models.api import Product
from src.models.domain import (
    CollectedProduct,
    CollectedShade,
    ShadeExtraction,
    SourceProduct,
    SourceShade,
)
from src.services.color_math import hex_to_hue_lightness, is_valid_hex
from src.services.interfaces.shade_repository import ShadeRepository

logger = get_logger("catalog")

CATALOG_RETAILER = "catalog"
CATALOG_QUERY = "catalog import"
_URL_KEYS = ("url-Official", "url-Amazon", "url-Ulta", "url-Sephora")


def _slug(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-") or "item"


def _unique(slug: str, taken: set[str]) -> str:
    candidate, n = slug, 2
    while candidate in taken:
        candidate, n = f"{slug}-{n}", n + 1
    taken.add(candidate)
    return candidate


def _extraction(hex_value: object) -> ShadeExtraction:
    if not isinstance(hex_value, str) or not is_valid_hex(hex_value):
        return ShadeExtraction(status="failed", error=f"Invalid hex in catalog: {hex_value!r}")
    normalized = hex_value.upper()
    hue, lightness = hex_to_hue_lightness(normalized)
    return ShadeExtraction(status="extracted", hex=normalized, hue=hue, lightness=lightness)


def parse_catalog(raw: object) -> list[CollectedProduct]:
    if not isinstance(raw, list):
        raise ValidationError("The catalog must be a JSON array of companies")
    collected: list[CollectedProduct] = []
    product_slugs: set[str] = set()
    for company in raw:
        brand = company.get("company")
        for item in company.get("products", []):
            name = item.get("name")
            if not brand or not name:
                raise ValidationError("Every catalog product needs a company and a name")
            shade_slugs: set[str] = set()
            shades = tuple(
                CollectedShade(
                    SourceShade(
                        asin=_unique(_slug(shade["name"]), shade_slugs),
                        name=shade["name"],
                        swatch_url=None,
                        undertone=shade.get("undertone") or None,
                    ),
                    _extraction(shade.get("hex")),
                )
                for shade in item.get("shades", [])
            )
            collected.append(
                CollectedProduct(
                    product=SourceProduct(
                        asin=_unique(_slug(f"{brand} {name}"), product_slugs),
                        title=name,
                        brand=brand,
                        detail_page_url=next((item[k] for k in _URL_KEYS if item.get(k)), None),
                        image_url=None,
                        retailer=CATALOG_RETAILER,
                    ),
                    shades=shades,
                )
            )
    return collected


def matches_query(product: Product, query: str) -> bool:
    """True when every word of the query appears in the product's brand or title."""
    haystack = f"{product.brand or ''} {product.title}".lower()
    return all(word in haystack for word in query.lower().split())


class CatalogImporter:
    def __init__(self, repository: ShadeRepository, path: Path) -> None:
        self._repository = repository
        self._path = path

    def import_catalog(self) -> tuple[str, list[Product]]:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as exc:
            raise ConfigurationError(f"Catalog file not found: {self._path}") from exc
        except json.JSONDecodeError as exc:
            raise ValidationError(f"The catalog is not valid JSON: {exc}") from exc

        products = parse_catalog(raw)
        self._repository.delete_unlisted(CATALOG_RETAILER, products)
        search_id, saved = self._repository.save_search(CATALOG_QUERY, products)
        logger.info("catalog_imported", products=len(saved))
        return search_id, saved
