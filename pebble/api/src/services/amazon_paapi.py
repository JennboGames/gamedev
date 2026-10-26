"""Amazon Product Advertising API 5.0 client (SearchItems + GetVariations, SigV4-signed).

HTTP transport, clock and sleep are injectable so the client is testable with recorded fixtures.
"""

import hashlib
import hmac
import json
import time
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from math import ceil
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.errors.error_types import ConfigurationError, UpstreamError
from src.logger import get_logger
from src.models.domain import AmazonProduct, AmazonShade
from src.services.config import AppConfig

logger = get_logger("amazon_paapi")

HttpPost = Callable[[str, dict[str, str], bytes], tuple[int, bytes]]

_SERVICE = "ProductAdvertisingAPI"
_TARGET_PREFIX = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1."
_ITEMS_PER_PAGE = 10
_MAX_SEARCH_PAGES = 10
_COLOR_ATTRIBUTES = {"color_name", "color", "colour", "colorname"}
_NO_VARIATIONS_CODES = {"InvalidParameterValue", "NoResults"}

_SEARCH_RESOURCES = [
    "ItemInfo.Title",
    "ItemInfo.ByLineInfo",
    "Images.Primary.Large",
    "ParentASIN",
]
_VARIATION_RESOURCES = ["ItemInfo.Title", "Images.Primary.Large", "VariationSummary.PageCount"]


class PaapiHttpError(UpstreamError):
    def __init__(self, status: int, api_code: str | None, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.api_code = api_code


def _urllib_post(url: str, headers: dict[str, str], body: bytes) -> tuple[int, bytes]:
    request = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()
    except (URLError, OSError) as exc:
        raise UpstreamError("Could not reach the Amazon Product Advertising API") from exc


def _hmac(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def sign_request(
    *,
    access_key: str,
    secret_key: str,
    host: str,
    region: str,
    path: str,
    target: str,
    payload: bytes,
    now: datetime,
) -> dict[str, str]:
    """AWS Signature V4 headers for a PA-API POST."""
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date = now.strftime("%Y%m%d")
    headers = {
        "content-encoding": "amz-1.0",
        "content-type": "application/json; charset=utf-8",
        "host": host,
        "x-amz-date": amz_date,
        "x-amz-target": target,
    }
    signed_headers = ";".join(sorted(headers))
    canonical_headers = "".join(f"{name}:{headers[name]}\n" for name in sorted(headers))
    canonical_request = "\n".join(
        ["POST", path, "", canonical_headers, signed_headers, hashlib.sha256(payload).hexdigest()]
    )
    scope = f"{date}/{region}/{_SERVICE}/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ]
    )
    key = _hmac(("AWS4" + secret_key).encode("utf-8"), date)
    for part in (region, _SERVICE, "aws4_request"):
        key = _hmac(key, part)
    signature = hmac.new(key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
    headers["Authorization"] = (
        f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )
    return headers


def _dig(data: Any, *path: str) -> Any:
    for key in path:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


class AmazonPaapiClient:
    def __init__(
        self,
        config: AppConfig,
        http_post: HttpPost = _urllib_post,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        sleep: Callable[[float], None] = time.sleep,
        min_interval_seconds: float = 1.0,
    ) -> None:
        self._config = config
        self._http_post = http_post
        self._clock = clock
        self._sleep = sleep
        self._min_interval = min_interval_seconds
        self._last_call: float | None = None

    def health_check(self) -> bool:
        c = self._config
        return bool(c.amazon_access_key and c.amazon_secret_key and c.amazon_partner_tag)

    def _credentials(self) -> tuple[str, str, str]:
        c = self._config
        if not (c.amazon_access_key and c.amazon_secret_key and c.amazon_partner_tag):
            raise ConfigurationError(
                "Amazon PA-API credentials are not configured "
                "(AMAZON_PAAPI_ACCESS_KEY, AMAZON_PAAPI_SECRET_KEY, AMAZON_PARTNER_TAG)"
            )
        return c.amazon_access_key, c.amazon_secret_key, c.amazon_partner_tag

    def _call(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        access_key, secret_key, partner_tag = self._credentials()
        body = json.dumps(
            {
                **payload,
                "PartnerTag": partner_tag,
                "PartnerType": "Associates",
                "Marketplace": self._config.amazon_marketplace,
            }
        ).encode("utf-8")
        host = self._config.amazon_host
        headers = sign_request(
            access_key=access_key,
            secret_key=secret_key,
            host=host,
            region=self._config.amazon_region,
            path=f"/paapi5/{operation.lower()}",
            target=_TARGET_PREFIX + operation,
            payload=body,
            now=self._clock(),
        )

        if self._last_call is not None:
            wait = self._min_interval - (time.monotonic() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = time.monotonic()

        status, raw = self._http_post(f"https://{host}/paapi5/{operation.lower()}", headers, body)
        try:
            data = json.loads(raw) if raw else {}
        except ValueError:
            data = {}
        if status != 200:
            error = (data.get("Errors") or [{}])[0]
            code = error.get("Code")
            message = error.get("Message") or f"Amazon PA-API returned HTTP {status}"
            logger.warning("paapi_error", operation=operation, status=status, code=code)
            raise PaapiHttpError(status, code, message)
        return data

    def search(self, query: str, max_products: int) -> list[AmazonProduct]:
        pinned = self._pinned_products()
        products: dict[str, AmazonProduct] = {}
        pages = min(ceil(max_products / _ITEMS_PER_PAGE), _MAX_SEARCH_PAGES)

        for page in range(1, pages + 1):
            data = self._call(
                "SearchItems",
                {
                    "Keywords": query,
                    "SearchIndex": "Beauty",
                    "ItemCount": _ITEMS_PER_PAGE,
                    "ItemPage": page,
                    "Resources": _SEARCH_RESOURCES,
                },
            )
            items = _dig(data, "SearchResult", "Items") or []
            for item in items:
                asin = item.get("ParentASIN") or item.get("ASIN")
                if not asin or asin in products or asin in pinned or len(products) >= max_products:
                    continue
                products[asin] = self._to_product(asin, item)
            if len(products) >= max_products or len(items) < _ITEMS_PER_PAGE:
                break

        return self._with_shades([*pinned.values(), *products.values()])

    def pinned_products(self) -> list[AmazonProduct]:
        return self._with_shades(self._pinned_products().values())

    def _with_shades(self, products: Iterable[AmazonProduct]) -> list[AmazonProduct]:
        return [
            AmazonProduct(
                asin=p.asin,
                title=p.title,
                brand=p.brand,
                detail_page_url=p.detail_page_url,
                image_url=p.image_url,
                shades=tuple(self._variations(p.asin)),
            )
            for p in products
        ]

    @staticmethod
    def _to_product(asin: str, item: dict[str, Any]) -> AmazonProduct:
        return AmazonProduct(
            asin=asin,
            title=_dig(item, "ItemInfo", "Title", "DisplayValue") or asin,
            brand=_dig(item, "ItemInfo", "ByLineInfo", "Brand", "DisplayValue"),
            detail_page_url=item.get("DetailPageURL"),
            image_url=_dig(item, "Images", "Primary", "Large", "URL"),
        )

    def _pinned_products(self) -> dict[str, AmazonProduct]:
        asins = list(self._config.pinned_asins)
        if not asins:
            return {}
        pinned: dict[str, AmazonProduct] = {}
        for start in range(0, len(asins), _ITEMS_PER_PAGE):
            try:
                data = self._call(
                    "GetItems",
                    {
                        "ItemIds": asins[start : start + _ITEMS_PER_PAGE],
                        "Resources": _SEARCH_RESOURCES,
                    },
                )
            except PaapiHttpError as exc:
                if exc.status != 400:
                    raise
                logger.warning("pinned_asins_unavailable", code=exc.api_code)
                continue
            for item in _dig(data, "ItemsResult", "Items") or []:
                asin = item.get("ParentASIN") or item.get("ASIN")
                if asin and asin not in pinned:
                    pinned[asin] = self._to_product(asin, item)
        return pinned

    def _variations(self, parent_asin: str) -> list[AmazonShade]:
        cap = self._config.max_shades_per_product
        shades: dict[str, AmazonShade] = {}
        page, page_count = 1, 1

        while page <= page_count and len(shades) < cap:
            try:
                data = self._call(
                    "GetVariations",
                    {
                        "ASIN": parent_asin,
                        "VariationCount": _ITEMS_PER_PAGE,
                        "VariationPage": page,
                        "Resources": _VARIATION_RESOURCES,
                    },
                )
            except PaapiHttpError as exc:
                if exc.status == 400 and exc.api_code in _NO_VARIATIONS_CODES:
                    break
                raise

            page_count = _dig(data, "VariationsResult", "VariationSummary", "PageCount") or 1
            for item in _dig(data, "VariationsResult", "Items") or []:
                asin = item.get("ASIN")
                if not asin or asin in shades:
                    continue
                shades[asin] = AmazonShade(
                    asin=asin,
                    name=self._shade_name(item) or asin,
                    swatch_url=_dig(item, "Images", "Primary", "Large", "URL"),
                )
            page += 1

        return list(shades.values())[:cap]

    @staticmethod
    def _shade_name(item: dict[str, Any]) -> str | None:
        for attribute in item.get("VariationAttributes") or []:
            if str(attribute.get("Name", "")).lower() in _COLOR_ATTRIBUTES and attribute.get(
                "Value"
            ):
                return attribute["Value"]
        return _dig(item, "ItemInfo", "Title", "DisplayValue")
