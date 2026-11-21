import pytest

from src.errors.error_types import UpstreamError
from src.services import amazon_creators
from src.services.amazon_creators import (
    API_BASE_URL,
    TOKEN_URL,
    AmazonCreatorsClient,
)
from src.services.config import AmazonCreatorsConfig

CONFIG = AmazonCreatorsConfig(
    client_id="the-client-id",
    client_secret="the-client-secret",
    partner_tag="pebble-20",
    marketplace="www.amazon.com",
)


class FakeHttp:
    def __init__(self, items_status: int = 200) -> None:
        self.calls: list[tuple[str, dict, dict]] = []
        self.items_status = items_status
        self.token_count = 0

    def __call__(self, url, headers, body):
        self.calls.append((url, headers, body))
        if url == TOKEN_URL:
            self.token_count += 1
            return 200, {"access_token": f"tok{self.token_count}", "expires_in": 3600}
        return self.items_status, {"itemsResult": {"items": []}}


class Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_get_items_sends_token_and_partner_tag():
    http = FakeHttp()
    client = AmazonCreatorsClient(CONFIG, http_post=http)

    result = client.get_items(["B09B2SBHQK"])

    assert result == {"itemsResult": {"items": []}}
    token_call, items_call = http.calls
    assert token_call[2]["client_id"] == "the-client-id"
    assert token_call[2]["scope"] == "creatorsapi::default"
    url, headers, body = items_call
    assert url == f"{API_BASE_URL}/catalog/v1/getItems"
    assert headers["Authorization"] == "Bearer tok1"
    assert headers["x-marketplace"] == "www.amazon.com"
    assert body["itemIds"] == ["B09B2SBHQK"]
    assert body["partnerTag"] == "pebble-20"


def test_token_is_cached_then_refreshed_near_expiry():
    http = FakeHttp()
    clock = Clock()
    client = AmazonCreatorsClient(CONFIG, http_post=http, clock=clock)

    client.get_items(["B09B2SBHQK"])
    client.get_items(["B09B2SBHQK"])
    assert http.token_count == 1

    clock.now = 3600 - 30  # inside the refresh margin
    client.get_items(["B09B2SBHQK"])
    assert http.token_count == 2


def test_unauthorized_response_drops_cached_token():
    http = FakeHttp(items_status=401)
    client = AmazonCreatorsClient(CONFIG, http_post=http)

    with pytest.raises(UpstreamError):
        client.get_items(["B09B2SBHQK"])
    http.items_status = 200
    client.get_items(["B09B2SBHQK"])

    assert http.token_count == 2


def test_token_failure_does_not_leak_credentials():
    def http(url, headers, body):
        return 401, {"error": "invalid_client", "error_description": "Client authentication failed"}

    client = AmazonCreatorsClient(CONFIG, http_post=http)

    with pytest.raises(UpstreamError) as caught:
        client.get_items(["B09B2SBHQK"])

    message = str(caught.value)
    assert "HTTP 401" in message
    assert "Client authentication failed" in message
    assert CONFIG.client_secret not in message


def test_get_client_requires_settings(monkeypatch):
    monkeypatch.setattr(amazon_creators, "_client", None)
    for name in (
        "AMAZON_CREATORS_CLIENT_ID",
        "AMAZON_CREATORS_CLIENT_SECRET",
        "AMAZON_CREATORS_PARTNER_TAG",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(Exception, match="AMAZON_CREATORS_CLIENT_ID"):
        amazon_creators.get_client()
