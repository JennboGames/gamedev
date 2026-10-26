import json
from datetime import datetime, timezone

import pytest

from src.errors.error_types import ConfigurationError, UpstreamError
from src.services.amazon_paapi import AmazonPaapiClient, PaapiHttpError, sign_request
from tests.conftest import load_fixture
from tests.mocks.config import make_config


class RecordedTransport:
    """Replays recorded PA-API responses and remembers every request."""

    def __init__(self, responses: dict[str, tuple[int, dict]]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, dict[str, str], dict]] = []

    def __call__(self, url: str, headers: dict[str, str], body: bytes) -> tuple[int, bytes]:
        self.requests.append((url, headers, json.loads(body)))
        status, payload = self.responses[url.rsplit("/", 1)[-1]]
        return status, json.dumps(payload).encode()


def make_client(transport, **config_overrides) -> AmazonPaapiClient:
    return AmazonPaapiClient(
        make_config(**config_overrides),
        http_post=transport,
        clock=lambda: datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc),
        sleep=lambda _seconds: None,
        min_interval_seconds=0,
    )


def recorded_transport() -> RecordedTransport:
    return RecordedTransport(
        {
            "searchitems": (200, load_fixture("paapi_search_items.json")),
            "getvariations": (200, load_fixture("paapi_get_variations.json")),
        }
    )


def test_search_returns_products_with_shades():
    client = make_client(recorded_transport())
    products = client.search("skin foundation", 20)

    assert [p.asin for p in products] == ["B0GQVP8RLD", "B0MOCKFM02"]
    double_wear = products[0]
    assert double_wear.brand == "Estée Lauder"
    assert [s.name for s in double_wear.shades][0] == "1N1 Ivory Nude"
    assert double_wear.shades[0].swatch_url.endswith("swatch-1n1.jpg")


def test_pinned_asins_are_included_first_and_not_duplicated():
    transport = recorded_transport()
    transport.responses["getitems"] = (
        200,
        {
            "ItemsResult": {
                "Items": [
                    {
                        "ASIN": "B0028P5TOW",
                        "ItemInfo": {
                            "Title": {"DisplayValue": "Luminous Silk Foundation"},
                            "ByLineInfo": {"Brand": {"DisplayValue": "Giorgio Armani"}},
                        },
                    },
                    {"ASIN": "B0GQVP8RLD", "ItemInfo": {"Title": {"DisplayValue": "Double Wear"}}},
                ]
            }
        },
    )
    client = make_client(transport, pinned_asins=("B0028P5TOW", "B0GQVP8RLD"))
    products = client.search("skin foundation", 1)

    get_items = next(body for url, _, body in transport.requests if url.endswith("/getitems"))
    assert get_items["ItemIds"] == ["B0028P5TOW", "B0GQVP8RLD"]
    assert [p.asin for p in products] == ["B0028P5TOW", "B0GQVP8RLD", "B0MOCKFM02"]
    assert products[0].brand == "Giorgio Armani"


def test_unavailable_pinned_asins_do_not_fail_the_search():
    transport = recorded_transport()
    transport.responses["getitems"] = (
        400,
        {"Errors": [{"Code": "InvalidParameterValue", "Message": "Unknown ASIN"}]},
    )
    products = make_client(transport, pinned_asins=("B0028P5TOW",)).search("foundation", 1)
    assert [p.asin for p in products] == ["B0GQVP8RLD"]


def test_shade_name_falls_back_to_title_without_color_attribute():
    products = make_client(recorded_transport()).search("foundation", 1)
    assert products[0].shades[1].name == "Double Wear 2W1 Dawn"


def test_search_respects_max_products():
    products = make_client(recorded_transport()).search("foundation", 1)
    assert len(products) == 1


def test_requests_are_signed_and_carry_partner_tag():
    transport = recorded_transport()
    make_client(transport).search("foundation", 1)

    url, headers, body = transport.requests[0]
    assert url == "https://webservices.amazon.com/paapi5/searchitems"
    assert headers["Authorization"].startswith(
        "AWS4-HMAC-SHA256 Credential=AKIATEST/20261026/us-east-1/"
    )
    assert body["PartnerTag"] == "tag-20"
    assert body["Keywords"] == "foundation"


def test_missing_credentials_raise_configuration_error_without_calling_amazon():
    transport = recorded_transport()
    client = make_client(transport, amazon_access_key=None)

    assert client.health_check() is False
    with pytest.raises(ConfigurationError):
        client.search("foundation", 1)
    assert transport.requests == []


def test_product_without_variations_has_no_shades():
    transport = recorded_transport()
    transport.responses["getvariations"] = (
        400,
        {"Errors": [{"Code": "InvalidParameterValue", "Message": "No variations"}]},
    )
    products = make_client(transport).search("foundation", 1)
    assert products[0].shades == ()


def test_amazon_errors_surface_as_upstream_errors():
    transport = recorded_transport()
    transport.responses["searchitems"] = (
        429,
        {"Errors": [{"Code": "TooManyRequests", "Message": "Slow down"}]},
    )
    with pytest.raises(UpstreamError) as caught:
        make_client(transport).search("foundation", 1)
    assert isinstance(caught.value, PaapiHttpError)
    assert caught.value.status == 429


def test_signature_is_deterministic():
    kwargs = dict(
        access_key="AKIATEST",
        secret_key="secret",
        host="webservices.amazon.com",
        region="us-east-1",
        path="/paapi5/searchitems",
        target="com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems",
        payload=b"{}",
        now=datetime(2026, 10, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert sign_request(**kwargs) == sign_request(**kwargs)
