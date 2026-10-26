import azure.functions as func

from src.functions._http import api_handler, json_response
from src.models.api import (
    ColorMap,
    ColorMapRequest,
    HealthResponse,
    Marker,
    Product,
    ProductList,
    SearchRequest,
    SearchResponse,
    Shade,
    ShadeList,
)

bp = func.Blueprint()

_MODELS = (
    Product,
    Shade,
    Marker,
    ColorMap,
    SearchRequest,
    SearchResponse,
    ProductList,
    ShadeList,
    ColorMapRequest,
    HealthResponse,
)

_ERROR_REF = {"$ref": "#/components/schemas/ErrorResponse"}


def _ref(name: str) -> dict:
    return {"$ref": f"#/components/schemas/{name}"}


def _json(name: str, description: str) -> dict:
    return {"description": description, "content": {"application/json": {"schema": _ref(name)}}}


def _error(description: str) -> dict:
    return {"description": description, "content": {"application/json": {"schema": _ERROR_REF}}}


def _id_param() -> dict:
    return {
        "name": "id",
        "in": "path",
        "required": True,
        "schema": {"type": "string", "format": "uuid"},
    }


def _schemas() -> dict:
    schemas: dict = {}
    for model in _MODELS:
        schema = model.model_json_schema(by_alias=True, ref_template="#/components/schemas/{model}")
        schemas.update(schema.pop("$defs", {}))
        schemas[model.__name__] = schema
    schemas["ErrorResponse"] = {
        "type": "object",
        "required": ["error"],
        "properties": {
            "error": {
                "type": "object",
                "required": ["code", "message"],
                "properties": {
                    "code": {
                        "type": "string",
                        "enum": [
                            "BAD_REQUEST",
                            "VALIDATION_ERROR",
                            "NOT_FOUND",
                            "UPSTREAM_ERROR",
                            "CONFIGURATION_ERROR",
                            "INTERNAL_ERROR",
                        ],
                    },
                    "message": {"type": "string"},
                    "details": {},
                },
            }
        },
    }
    return schemas


def build_openapi_spec() -> dict:
    body = lambda name: {  # noqa: E731
        "required": True,
        "content": {"application/json": {"schema": _ref(name)}},
    }
    return {
        "openapi": "3.0.3",
        "info": {"title": "Foundation Collector API", "version": "1.0.0"},
        "servers": [{"url": "/api"}],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {
                        "200": _json("HealthResponse", "healthy or degraded"),
                        "503": _json("HealthResponse", "unhealthy"),
                    },
                }
            },
            "/searches": {
                "post": {
                    "summary": "Search Amazon, store products and shades, extract hex per shade",
                    "requestBody": body("SearchRequest"),
                    "responses": {
                        "201": _json("SearchResponse", "Search collected"),
                        "422": _error("Validation failed"),
                        "502": _error("Amazon or image host failed"),
                    },
                }
            },
            "/products": {
                "get": {
                    "summary": "List collected products",
                    "responses": {"200": _json("ProductList", "Products")},
                }
            },
            "/products/{id}": {
                "get": {
                    "summary": "Get one product",
                    "parameters": [_id_param()],
                    "responses": {
                        "200": _json("Product", "Product"),
                        "404": _error("Not found"),
                        "422": _error("Invalid id"),
                    },
                }
            },
            "/products/{id}/shades": {
                "get": {
                    "summary": "List shades of a product",
                    "parameters": [_id_param()],
                    "responses": {
                        "200": _json("ShadeList", "Shades"),
                        "404": _error("Not found"),
                        "422": _error("Invalid id"),
                    },
                }
            },
            "/shades/{id}/extract-hex": {
                "post": {
                    "summary": "Re-download the swatch and re-extract its hex",
                    "parameters": [_id_param()],
                    "responses": {
                        "200": _json("Shade", "Updated shade"),
                        "404": _error("Not found"),
                        "422": _error("Invalid id"),
                        "502": _error("Swatch could not be downloaded"),
                    },
                }
            },
            "/color-map": {
                "post": {
                    "summary": "Generate the color map and plot all shades",
                    "requestBody": {
                        "required": False,
                        "content": {"application/json": {"schema": _ref("ColorMapRequest")}},
                    },
                    "responses": {
                        "201": _json("ColorMap", "Color map generated"),
                        "404": _error("No shades with an extracted hex"),
                        "422": _error("Validation failed"),
                    },
                },
                "get": {
                    "summary": "Latest color map",
                    "responses": {
                        "200": _json("ColorMap", "Color map"),
                        "404": _error("No color map generated yet"),
                    },
                },
            },
        },
        "components": {"schemas": _schemas()},
    }


@bp.route(route="openapi.json", methods=["GET"], auth_level=func.AuthLevel.ANONYMOUS)
@api_handler
def openapi_spec(req: func.HttpRequest) -> func.HttpResponse:
    return json_response(build_openapi_spec())
