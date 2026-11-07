import json
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from src.models.domain import SourceProduct, SourceShade
from src.services.color_extractor import PillowColorExtractor
from src.services.registry import ServiceRegistry, clear_services, register_services
from tests.mocks.fakes import FakeBlobStore, FakeImageFetcher, FakeProductSearch
from tests.mocks.mock_repository import InMemoryShadeRepository

FIXTURES = Path(__file__).parent / "fixtures"


def make_png(color: tuple[int, int, int], size: tuple[int, int] = (32, 32)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


IVORY = (241, 210, 181)
TRUFFLE = (122, 74, 50)

IVORY_URL = "https://images.ulta.com/is/image/ivory.png"
TRUFFLE_URL = "https://images.ulta.com/is/image/truffle.png"
BROKEN_URL = "https://images.ulta.com/is/image/missing.png"


@pytest.fixture
def retailer_products() -> list[SourceProduct]:
    return [
        SourceProduct(
            asin="B0GQVP8RLD",
            title="Double Wear Stay-in-Place Foundation",
            brand="Estée Lauder",
            detail_page_url="https://www.ulta.com/p/double-wear",
            image_url="https://images.ulta.com/is/image/double-wear.jpg",
            retailer="ulta",
            shades=(
                SourceShade(asin="S1", name="1N1 Ivory Nude", swatch_url=IVORY_URL),
                SourceShade(asin="S2", name="6N2 Truffle", swatch_url=TRUFFLE_URL),
                SourceShade(asin="S3", name="3C2 Pebble", swatch_url=BROKEN_URL),
            ),
        )
    ]


@pytest.fixture
def services(retailer_products: list[SourceProduct]) -> ServiceRegistry:
    registry = ServiceRegistry(
        repository=InMemoryShadeRepository(),
        blob_store=FakeBlobStore(),
        product_search=FakeProductSearch(retailer_products),
        image_fetcher=FakeImageFetcher(
            {IVORY_URL: make_png(IVORY), TRUFFLE_URL: make_png(TRUFFLE)}
        ),
        color_extractor=PillowColorExtractor(),
        extraction_workers=2,
    )
    register_services(registry)
    yield registry
    clear_services()
