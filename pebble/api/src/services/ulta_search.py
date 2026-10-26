"""Ulta product search from the public foundation listing and product pages.

Ulta has no public API. The foundation category page is server-rendered and each product page
carries schema.org JSON-LD with one variant per shade, so this reads those pages with plain,
rate-limited HTTP requests. A block (HTTP 403/429) is reported as an error; it is never worked around.
HTTP transport and sleep are injectable so the parsing is testable with recorded pages.
"""

import json
import re
import time
import unicodedata
from collections.abc import Callable
from html import unescape
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.errors.error_types import UpstreamError
from src.logger import get_logger
from src.models.domain import AmazonProduct, AmazonShade

logger = get_logger("ulta_search")

HttpGet = Callable[[str, dict[str, str]], tuple[int, bytes]]

LISTING_URL = "https://www.ulta.com/shop/makeup/face/foundation"
_PRODUCT_URL_PREFIX = "https://www.ulta.com/p/"
_SWATCH_URL = "https://media.ultainc.com/i/ulta/{sku}_sw?w=80"
_USER_AGENT = "Mozilla/5.0 (compatible; PebbleShadeBot/1.0)"

_CARD_LINK = re.compile(r'href="(https://www\.ulta\.com/p/[^"?#]+)[^"]*"')
_BRAND = re.compile(r'pal-c-ProductCardBody--brandName"[^>]*>\s*<p[^>]*>(.*?)</p>', re.S)
_TITLE = re.compile(r'pal-c-ProductCardBody--title"[^>]*>\s*<p[^>]*>(.*?)</p>', re.S)
_JSON_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
_SKU = re.compile(r"[A-Za-z0-9_-]+")
_GENERIC_WORDS = {"foundation", "foundations", "skin", "makeup", "face", "the", "a", "and", "for"}


def _urllib_get(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:  # noqa: S310
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()
    except (URLError, OSError) as exc:
        raise UpstreamError("Could not reach Ulta") from exc


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def _text(fragment: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def parse_listing(html: str) -> list[tuple[str, str | None, str]]:
    """(product url, brand, title) for each product tile, in page order."""
    first_seen: dict[str, int] = {}
    for match in _CARD_LINK.finditer(html):
        first_seen.setdefault(match.group(1), match.start())
    ordered = sorted(first_seen.items(), key=lambda item: item[1])

    tiles: list[tuple[str, str | None, str]] = []
    for index, (url, start) in enumerate(ordered):
        end = ordered[index + 1][1] if index + 1 < len(ordered) else len(html)
        window = html[start:end]
        title = _TITLE.search(window)
        if title is None:
            continue
        brand = _BRAND.search(window)
        tiles.append((url, _text(brand.group(1)) if brand else None, _text(title.group(1))))
    return tiles


def matches_query(query: str, brand: str | None, title: str) -> bool:
    """Every non-generic word of the query must appear in the product's brand or title."""
    words = [w for w in re.findall(r"\w+", _fold(query)) if w not in _GENERIC_WORDS]
    haystack = _fold(f"{brand or ''} {title}")
    return all(word in haystack for word in words)


def _json_ld_blocks(html: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for raw in _JSON_LD.findall(html):
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        blocks.extend(
            item for item in (data if isinstance(data, list) else [data]) if isinstance(item, dict)
        )
    return blocks


def parse_product_page(html: str, url: str, max_shades: int) -> AmazonProduct | None:
    blocks = _json_ld_blocks(html)
    product = next((b for b in blocks if b.get("@type") == "Product" and b.get("productID")), None)
    group = next((b for b in blocks if b.get("@type") == "ProductGroup"), None)
    if product is None and group is None:
        return None

    info = product or group or {}
    brand = info.get("brand")
    if isinstance(brand, dict):
        brand = brand.get("name")

    shades: dict[str, AmazonShade] = {}
    for variant in (group or {}).get("hasVariant") or []:
        sku = str(variant.get("sku") or "")
        if not _SKU.fullmatch(sku) or sku in shades:
            continue
        name = (variant.get("color") or variant.get("name") or sku).strip()
        shades[sku] = AmazonShade(asin=sku, name=name, swatch_url=_SWATCH_URL.format(sku=sku))
        if len(shades) >= max_shades:
            break

    sku = str(info.get("sku") or "")
    asin = str((product or {}).get("productID") or (group or {}).get("productGroupID") or "")
    if not asin:
        return None
    return AmazonProduct(
        asin=asin,
        title=info.get("name") or asin,
        brand=brand if isinstance(brand, str) else None,
        detail_page_url=url,
        image_url=f"https://media.ulta.com/i/ulta/{sku}?w=500&h=500"
        if _SKU.fullmatch(sku)
        else None,
        shades=tuple(shades.values()),
        retailer="ulta",
    )


class UltaSearch:
    def __init__(
        self,
        http_get: HttpGet = _urllib_get,
        sleep: Callable[[float], None] = time.sleep,
        min_interval_seconds: float = 1.0,
        max_shades: int = 60,
    ) -> None:
        self._http_get = http_get
        self._sleep = sleep
        self._min_interval = min_interval_seconds
        self._max_shades = max_shades
        self._last_call: float | None = None

    def health_check(self) -> bool:
        return True

    def _get(self, url: str) -> str:
        if self._last_call is not None:
            wait = self._min_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = time.monotonic()

        status, body = self._http_get(url, {"User-Agent": _USER_AGENT, "Accept": "text/html"})
        if status in (403, 429):
            raise UpstreamError(f"Ulta blocked automated access (HTTP {status})")
        if status != 200:
            raise UpstreamError(f"Ulta returned HTTP {status}")
        return body.decode("utf-8", errors="replace")

    def search(self, query: str, max_products: int) -> list[AmazonProduct]:
        tiles = [
            t for t in parse_listing(self._get(LISTING_URL)) if matches_query(query, t[1], t[2])
        ]
        products: list[AmazonProduct] = []
        for url, _brand, _title in tiles[:max_products]:
            if not url.startswith(_PRODUCT_URL_PREFIX):
                continue
            product = parse_product_page(self._get(url), url, self._max_shades)
            if product is None:
                logger.warning("ulta_product_unparsed", url=url)
                continue
            products.append(product)
        return products
