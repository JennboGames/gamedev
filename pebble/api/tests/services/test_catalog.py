import json

import pytest

from src.errors.error_types import ConfigurationError, ValidationError
from src.services.catalog import CATALOG_RETAILER, CatalogImporter, parse_catalog
from src.services.collector import ColorMapService
from src.services.color_map import ColorMapRenderer
from tests.mocks.fakes import FakeBlobStore
from tests.mocks.mock_repository import InMemoryShadeRepository

CATALOG = [
    {
        "company": "Estee Lauder",
        "products": [
            {
                "name": "Double Wear",
                "url-Ulta": "https://www.ulta.com/p/double-wear",
                "shades": [
                    {"name": "1N1 Ivory Nude", "undertone": "neutral", "hex": "#edc8ae"},
                    {"name": "1N1 Ivory Nude", "undertone": "neutral", "hex": "#d8b39d"},
                    {"name": "Broken", "hex": "nope"},
                ],
            }
        ],
    },
    {"company": "Haus Labs", "products": [{"name": "Triclone", "shades": []}]},
]


def test_parse_catalog_builds_catalog_products_with_uppercase_hex():
    first, second = parse_catalog(CATALOG)

    assert first.product.retailer == CATALOG_RETAILER
    assert first.product.brand == "Estee Lauder"
    assert first.product.asin == "estee-lauder-double-wear"
    assert first.product.detail_page_url == "https://www.ulta.com/p/double-wear"
    assert second.product.detail_page_url is None

    ivory, duplicate, broken = first.shades
    assert ivory.extraction.status == "extracted"
    assert ivory.extraction.hex == "#EDC8AE"
    assert ivory.extraction.hue is not None and ivory.extraction.lightness is not None
    assert (ivory.shade.asin, duplicate.shade.asin) == ("1n1-ivory-nude", "1n1-ivory-nude-2")
    assert broken.extraction.status == "failed"
    assert (ivory.shade.undertone, broken.shade.undertone) == ("neutral", None)


def test_parse_catalog_rejects_a_non_array():
    with pytest.raises(ValidationError):
        parse_catalog({"company": "x"})


def test_import_is_idempotent_and_reports_partial_products(tmp_path):
    path = tmp_path / "products.json"
    path.write_text(json.dumps(CATALOG), encoding="utf-8")
    repository = InMemoryShadeRepository()
    importer = CatalogImporter(repository, path)

    _, products = importer.import_catalog()
    importer.import_catalog()

    assert [p.status for p in products] == ["partial", "collected"]
    assert len(repository.products) == 2
    assert len(repository.shades) == 3


def test_import_missing_file_is_a_configuration_error(tmp_path):
    with pytest.raises(ConfigurationError):
        CatalogImporter(InMemoryShadeRepository(), tmp_path / "missing.json").import_catalog()


def test_color_map_can_be_limited_to_catalog_products(tmp_path, services):
    path = tmp_path / "products.json"
    path.write_text(json.dumps(CATALOG), encoding="utf-8")
    CatalogImporter(services.repository, path).import_catalog()
    services.collector().collect("skin foundation", 5)  # adds an Amazon product

    everything = services.color_maps().generate(None)
    catalog_only = ColorMapService(
        services.repository, FakeBlobStore(), ColorMapRenderer(), CATALOG_RETAILER
    ).generate(None)

    assert len(everything.markers) == 4
    assert {m.product_title for m in catalog_only.markers} == {"Double Wear"}


def test_reimport_removes_shades_and_products_no_longer_in_the_catalog(tmp_path, services):
    path = tmp_path / "products.json"
    path.write_text(json.dumps(CATALOG), encoding="utf-8")
    importer = CatalogImporter(services.repository, path)
    importer.import_catalog()
    services.collector().collect("skin foundation", 5)  # an Amazon product that must survive

    double_wear = CATALOG[0]["products"][0]
    trimmed = [
        {
            "company": "Estee Lauder",
            "products": [{**double_wear, "shades": double_wear["shades"][:1]}],
        }
    ]
    path.write_text(json.dumps(trimmed), encoding="utf-8")
    _, products = importer.import_catalog()

    assert [(p.title, p.shade_count) for p in products] == [("Double Wear", 1)]
    titles = sorted(p.title for p in services.repository.list_products())
    assert titles == ["Double Wear", "Double Wear Stay-in-Place Foundation"]
    assert len(services.repository.shades) == 1 + 3  # one catalog shade plus the Amazon product's
