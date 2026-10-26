"""Downloads swatch images from known retailer image hosts only (HTTPS, no redirects, size-capped)."""

from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from src.errors.error_types import UpstreamError
from src.models.domain import FetchedImage

ALLOWED_HOST_SUFFIXES = (
    ".media-amazon.com",
    ".ssl-images-amazon.com",
    ".images-amazon.com",
    ".ultainc.com",
    ".ulta.com",
)
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # noqa: ANN002, ANN003, ANN201
        return None


class HttpImageFetcher:
    def __init__(
        self,
        allowed_host_suffixes: tuple[str, ...] = ALLOWED_HOST_SUFFIXES,
        max_bytes: int = MAX_IMAGE_BYTES,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._allowed = allowed_host_suffixes
        self._max_bytes = max_bytes
        self._timeout = timeout_seconds
        self._opener = build_opener(_NoRedirect)

    def _check_url(self, url: str) -> None:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not any(host.endswith(s) for s in self._allowed):
            raise UpstreamError("The swatch image URL is not an allowed retailer image host")

    def fetch(self, url: str) -> FetchedImage:
        self._check_url(url)
        try:
            with self._opener.open(Request(url), timeout=self._timeout) as response:  # noqa: S310
                content_type = response.headers.get_content_type()
                data = response.read(self._max_bytes + 1)
        except (URLError, OSError) as exc:
            raise UpstreamError("The swatch image could not be downloaded") from exc

        if len(data) > self._max_bytes:
            raise UpstreamError("The swatch image is too large")
        if not content_type.startswith("image/"):
            raise UpstreamError("The swatch URL did not return an image")
        return FetchedImage(data=data, content_type=content_type)
