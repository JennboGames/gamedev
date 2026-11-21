import json

import azure.functions as func
import pytest

from src.errors.error_types import UpstreamError
from src.functions import amazon_items


class FakeClient:
    def __init__(self, error: Exception | None = None) -> None:
        self.asins: list[str] | None = None
        self.error = error

    def get_items(self, asins):
        if self.error:
            raise self.error
        self.asins = asins
        return {"itemsResult": {"items": [{"asin": asins[0]}]}}


def post(body) -> func.HttpResponse:
    request = func.HttpRequest(
        method="POST",
        url="http://localhost:7071/api/experimental/amazon/items",
        route_params={},
        body=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    return amazon_items.amazon_items._function.get_user_function()(request)


def test_returns_amazon_payload_with_normalized_asins(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(amazon_items, "get_client", lambda: client)

    response = post({"asins": [" b09b2sbhk4 ", "B09B2SBHK4"]})

    assert response.status_code == 200
    assert json.loads(response.get_body())["itemsResult"]["items"][0]["asin"] == "B09B2SBHK4"
    assert client.asins == ["B09B2SBHK4"]


@pytest.mark.parametrize(
    "body", [{"asins": []}, {"asins": ["short"]}, {"asins": ["B09B2SBHK4"] * 11}, {}]
)
def test_rejects_invalid_asins(monkeypatch, body):
    monkeypatch.setattr(amazon_items, "get_client", lambda: FakeClient())

    assert post(body).status_code == 422


def test_upstream_failure_maps_to_502(monkeypatch):
    monkeypatch.setattr(
        amazon_items,
        "get_client",
        lambda: FakeClient(UpstreamError("Amazon GetItems request failed (HTTP 429)")),
    )

    response = post({"asins": ["B09B2SBHK4"]})

    assert response.status_code == 502
    assert json.loads(response.get_body())["error"]["code"] == "UPSTREAM_ERROR"
