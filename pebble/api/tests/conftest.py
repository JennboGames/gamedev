import json
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from src.models.domain import AmazonProduct, AmazonShade
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

IVORY_URL = "https://m.media-amazon.com/images/I/ivory.png"
TRUFFLE_URL = "https://m.media-amazon.com/images/I/truffle.png"
BROKEN_URL = "https://m.media-amazon.com/images/I/missing.png"


@pytest.fixture
def amazon_products() -> list[AmazonProduct]:
    return [
        AmazonProduct(
            asin="B0GQVP8RLD",
            title="Double Wear Stay-in-Place Foundation",
            brand="Estée Lauder",
            detail_page_url="https://www.amazon.com/dp/B0GQVP8RLD",
            image_url="https://m.media-amazon.com/images/I/double-wear.jpg",
            shades=(
                AmazonShade(asin="S1", name="1N1 Ivory Nude", swatch_url=IVORY_URL),
                AmazonShade(asin="S2", name="6N2 Truffle", swatch_url=TRUFFLE_URL),
                AmazonShade(asin="S3", name="3C2 Pebble", swatch_url=BROKEN_URL),
            ),
        )
    ]


@pytest.fixture
def services(amazon_products: list[AmazonProduct]) -> ServiceRegistry:
    registry = ServiceRegistry(
        repository=InMemoryShadeRepository(),
        blob_store=FakeBlobStore(),
        product_search=FakeProductSearch(amazon_products),
        image_fetcher=FakeImageFetcher(
            {IVORY_URL: make_png(IVORY), TRUFFLE_URL: make_png(TRUFFLE)}
        ),
        color_extractor=PillowColorExtractor(),
        extraction_workers=2,
    )
    register_services(registry)
    yield registry
    clear_services()
