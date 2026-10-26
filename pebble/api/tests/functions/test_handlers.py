import json

import azure.functions as func
import pytest

from src.functions import (
    create_color_map,
    create_search,
    extract_shade_hex,
    get_color_map,
    get_product,
    health,
    list_product_shades,
    list_products,
    openapi,
)
from src.functions.health import compute_health_status


def call(
    module, name: str, *, method: str = "GET", route_params=None, body=None
) -> func.HttpResponse:
    request = func.HttpRequest(
        method=method,
        url=f"http://localhost:7071/api/{name}",
        route_params=route_params or {},
        body=json.dumps(body).encode() if body is not None else b"",
        headers={"content-type": "application/json"},
    )
    handler = getattr(module, name)._function.get_user_function()
    return handler(request)


def json_of(response: func.HttpResponse) -> dict:
    return json.loads(response.get_body())


def collect(services) -> dict:
    response = call(
        create_search, "create_search", method="POST", body={"query": "skin foundation"}
    )
    assert response.status_code == 201
    return json_of(response)


def test_create_search_returns_201_with_products(services):
    body = collect(services)

    assert body["searchId"]
    product = body["products"][0]
    assert product["title"].startswith("Double Wear")
    assert product["shadeCount"] == 3
    assert product["status"] == "partial"
    assert product["retailer"] == "amazon"
    assert body["warnings"] == []
    assert services.product_search.calls[-1][2] == ("amazon",)


def test_create_search_passes_selected_retailers_and_returns_warnings(services):
    services.product_search.warnings = ["Sephora: blocked"]
    response = call(
        create_search,
        "create_search",
        method="POST",
        body={"query": "foundation", "retailers": ["amazon", "sephora"]},
    )

    assert response.status_code == 201
    assert json_of(response)["warnings"] == ["Sephora: blocked"]
    assert services.product_search.calls[-1][2] == ("amazon", "sephora")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"query": ""},
        {"query": "x"},
        {"query": "foundation", "maxProducts": 0},
        {"query": "foundation", "maxProducts": 51},
        {"query": "foundation", "retailers": []},
        {"query": "foundation", "retailers": ["walmart"]},
    ],
)
def test_create_search_validates_input(services, payload):
    response = call(create_search, "create_search", method="POST", body=payload)

    assert response.status_code == 422
    error = json_of(response)["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"]


def test_create_search_rejects_invalid_json(services):
    request = func.HttpRequest(
        method="POST", url="http://localhost/api/searches", body=b"{nope", route_params={}
    )
    response = create_search.create_search._function.get_user_function()(request)
    assert response.status_code == 400
    assert json_of(response)["error"]["code"] == "BAD_REQUEST"


def test_list_products_and_get_product(services):
    product = collect(services)["products"][0]

    listed = json_of(call(list_products, "list_products"))
    assert [p["id"] for p in listed["items"]] == [product["id"]]

    fetched = call(get_product, "get_product", route_params={"id": product["id"]})
    assert fetched.status_code == 200
    assert json_of(fetched)["asin"] == "B0GQVP8RLD"


def test_get_product_unknown_is_404(services):
    response = call(
        get_product, "get_product", route_params={"id": "00000000-0000-0000-0000-000000000000"}
    )
    assert response.status_code == 404
    assert json_of(response)["error"]["code"] == "NOT_FOUND"


def test_get_product_rejects_malformed_id(services):
    response = call(get_product, "get_product", route_params={"id": "not-a-uuid"})
    assert response.status_code == 422


def test_list_product_shades(services):
    product = collect(services)["products"][0]

    response = call(list_product_shades, "list_product_shades", route_params={"id": product["id"]})

    assert response.status_code == 200
    shades = json_of(response)["items"]
    assert len(shades) == 3
    assert {s["name"] for s in shades} == {"1N1 Ivory Nude", "6N2 Truffle", "3C2 Pebble"}


def test_list_product_shades_unknown_product_is_404(services):
    response = call(
        list_product_shades,
        "list_product_shades",
        route_params={"id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


def test_extract_shade_hex_unknown_is_404(services):
    response = call(
        extract_shade_hex,
        "extract_shade_hex",
        method="POST",
        route_params={"id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


def test_extract_shade_hex_failure_is_502(services):
    product = collect(services)["products"][0]
    shades = json_of(
        call(list_product_shades, "list_product_shades", route_params={"id": product["id"]})
    )["items"]
    failed = next(s for s in shades if s["status"] == "failed")

    response = call(
        extract_shade_hex, "extract_shade_hex", method="POST", route_params={"id": failed["id"]}
    )

    assert response.status_code == 502
    assert json_of(response)["error"]["code"] == "UPSTREAM_ERROR"


def test_color_map_requires_shades(services):
    assert call(create_color_map, "create_color_map", method="POST").status_code == 404
    assert call(get_color_map, "get_color_map").status_code == 404


def test_create_and_get_color_map(services):
    collect(services)

    created = call(create_color_map, "create_color_map", method="POST")
    assert created.status_code == 201
    body = json_of(created)
    assert body["width"] > 0 and body["height"] > 0
    assert len(body["markers"]) == 2
    marker = body["markers"][0]
    assert {"shadeId", "productId", "shadeName", "productTitle", "hex", "x", "y"} <= marker.keys()
    assert 0 <= marker["x"] <= 1 and 0 <= marker["y"] <= 1

    latest = call(get_color_map, "get_color_map")
    assert latest.status_code == 200
    assert json_of(latest)["imageUrl"] == body["imageUrl"]


def test_create_color_map_validates_product_ids(services):
    response = call(
        create_color_map, "create_color_map", method="POST", body={"productIds": ["nope"]}
    )
    assert response.status_code == 422


def test_health_healthy(services):
    response = call(health, "health")
    assert response.status_code == 200
    assert json_of(response) == {
        "status": "healthy",
        "services": {"database": True, "storage": True, "amazon": True},
    }


def test_health_degraded_still_returns_200(services):
    services.product_search.configured = False
    response = call(health, "health")
    assert response.status_code == 200
    assert json_of(response)["status"] == "degraded"


def test_health_unhealthy_returns_503(services):
    services.repository.healthy = False
    services.blob_store.healthy = False
    services.product_search.configured = False
    response = call(health, "health")
    assert response.status_code == 503
    assert json_of(response)["status"] == "unhealthy"


def test_compute_health_status():
    assert compute_health_status({"a": True, "b": True}) == "healthy"
    assert compute_health_status({"a": True, "b": False}) == "degraded"
    assert compute_health_status({"a": False, "b": False}) == "unhealthy"


def test_openapi_documents_every_route(services):
    spec = json_of(call(openapi, "openapi_spec"))
    paths = set(spec["paths"])
    assert {
        "/health",
        "/searches",
        "/products",
        "/products/{id}",
        "/products/{id}/shades",
        "/shades/{id}/extract-hex",
        "/color-map",
    } <= paths
