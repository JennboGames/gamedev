from collections.abc import Sequence

from src.errors.error_types import UpstreamError
from src.models.domain import AmazonProduct, FetchedImage, SearchOutcome


class FakeBlobStore:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], tuple[bytes, str]] = {}
        self.healthy = True

    def upload(self, container: str, name: str, data: bytes, content_type: str) -> None:
        self.objects[(container, name)] = (data, content_type)

    def read_url(self, container: str, name: str) -> str:
        return f"https://blob.test/{container}/{name}"

    def health_check(self) -> bool:
        return self.healthy


class FakeProductSearch:
    def __init__(
        self,
        products: list[AmazonProduct] | None = None,
        configured: bool = True,
        warnings: list[str] | None = None,
    ) -> None:
        self.products = products or []
        self.configured = configured
        self.warnings = warnings or []
        self.calls: list[tuple[str, int, tuple[str, ...]]] = []

    def search(
        self, query: str, max_products: int, retailers: Sequence[str] = ("amazon",)
    ) -> SearchOutcome:
        self.calls.append((query, max_products, tuple(retailers)))
        return SearchOutcome(products=self.products[:max_products], warnings=list(self.warnings))

    def health_check(self) -> bool:
        return self.configured


class FakeImageFetcher:
    """Serves images by URL; unknown URLs fail the way a blocked or missing download would."""

    def __init__(self, images: dict[str, bytes] | None = None) -> None:
        self.images = images or {}

    def fetch(self, url: str) -> FetchedImage:
        if url not in self.images:
            raise UpstreamError("The swatch image could not be downloaded")
        return FetchedImage(data=self.images[url], content_type="image/png")
