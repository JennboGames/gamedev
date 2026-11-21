"""Amazon Creators API client (experimental): Login with Amazon token + catalog GetItems.

The client id and secret come from app settings that Key Vault references fill in. They are only
ever sent to Amazon and never logged or returned. HTTP transport and clock are injectable for tests.
"""

import json
import threading
import time
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.errors.error_types import UpstreamError
from src.logger import get_logger
from src.services.config import AmazonCreatorsConfig, load_amazon_config

logger = get_logger("amazon_creators")

TOKEN_URL = "https://api.amazon.com/auth/o2/token"  # noqa: S105
API_BASE_URL = "https://creatorsapi.amazon"
GET_ITEMS_RESOURCES = [
    "images.primary.medium",
    "itemInfo.title",
    "itemInfo.byLineInfo",
    "itemInfo.features",
    "offersV2.listings.price",
    "parentASIN",
]
_TOKEN_REFRESH_MARGIN_SECONDS = 60
_MAX_MESSAGE_LENGTH = 200

HttpPost = Callable[[str, dict[str, str], dict[str, Any]], tuple[int, Any]]


def _urllib_post(url: str, headers: dict[str, str], body: dict[str, Any]) -> tuple[int, Any]:
    request = Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")  # noqa: S310
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310
            status, raw = response.status, response.read()
    except HTTPError as exc:
        status, raw = exc.code, exc.read()
    except (URLError, OSError) as exc:
        raise UpstreamError("Could not reach Amazon") from exc
    try:
        return status, json.loads(raw)
    except ValueError:
        return status, None


def _failure(action: str, status: int, body: Any) -> UpstreamError:
    # Amazon's error text never contains our credentials, so it is safe to relay for diagnosis.
    detail = ""
    if isinstance(body, dict):
        text = body.get("message") or body.get("error_description") or body.get("error")
        if isinstance(text, str):
            detail = f": {text[:_MAX_MESSAGE_LENGTH]}"
    return UpstreamError(f"Amazon {action} failed (HTTP {status}){detail}")


class AmazonCreatorsClient:
    def __init__(
        self,
        config: AmazonCreatorsConfig,
        http_post: HttpPost = _urllib_post,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._config = config
        self._http_post = http_post
        self._clock = clock
        self._lock = threading.Lock()
        self._token: str | None = None
        self._expires_at = 0.0

    def _access_token(self) -> str:
        with self._lock:
            if self._token and self._clock() < self._expires_at - _TOKEN_REFRESH_MARGIN_SECONDS:
                return self._token
            status, body = self._http_post(
                TOKEN_URL,
                {"Content-Type": "application/json"},
                {
                    "grant_type": "client_credentials",
                    "client_id": self._config.client_id,
                    "client_secret": self._config.client_secret,
                    "scope": "creatorsapi::default",
                },
            )
            token = body.get("access_token") if isinstance(body, dict) else None
            if status != 200 or not isinstance(token, str) or not token:
                raise _failure("token request", status, body)
            expires_in = body.get("expires_in")
            lifetime = float(expires_in) if isinstance(expires_in, int | float) else 3600.0
            self._token = token
            self._expires_at = self._clock() + lifetime
            return token

    def _invalidate_token(self) -> None:
        with self._lock:
            self._token = None

    def get_items(self, asins: list[str]) -> dict[str, Any]:
        token = self._access_token()
        status, body = self._http_post(
            f"{API_BASE_URL}/catalog/v1/getItems",
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "x-marketplace": self._config.marketplace,
            },
            {
                "itemIds": asins,
                "itemIdType": "ASIN",
                "marketplace": self._config.marketplace,
                "partnerTag": self._config.partner_tag,
                "resources": GET_ITEMS_RESOURCES,
            },
        )
        if status in (401, 403):
            self._invalidate_token()
        if status != 200 or not isinstance(body, dict):
            logger.warning("get_items_failed", status=status)
            raise _failure("GetItems request", status, body)
        return body


_client: AmazonCreatorsClient | None = None
_client_lock = threading.Lock()


def get_client() -> AmazonCreatorsClient:
    global _client
    with _client_lock:
        if _client is None:
            _client = AmazonCreatorsClient(load_amazon_config())
        return _client
