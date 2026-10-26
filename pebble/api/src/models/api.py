"""Wire contracts (camelCase JSON). Mirrors plan route definitions."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

ProductStatus = Literal["collected", "extracting", "partial"]
ShadeStatus = Literal["extracted", "failed"]
Retailer = Literal["amazon", "ulta", "sephora"]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    def to_json(self) -> dict:
        return self.model_dump(mode="json", by_alias=True)


class Product(ApiModel):
    id: UUID
    retailer: Retailer = "amazon"
    asin: str
    title: str
    brand: str | None = None
    detail_page_url: str | None = None
    image_url: str | None = None
    shade_count: int
    sample_hexes: list[str] = Field(default_factory=list)
    status: ProductStatus
    created_at: datetime


class Shade(ApiModel):
    id: UUID
    product_id: UUID
    asin: str
    name: str
    swatch_url: str | None = None
    hex: str | None = None
    hue: float | None = None
    lightness: float | None = None
    status: ShadeStatus
    error: str | None = None


class Marker(ApiModel):
    shade_id: UUID
    product_id: UUID
    shade_name: str
    product_title: str
    hex: str
    hue: float
    lightness: float
    x: float
    y: float


class ColorMap(ApiModel):
    image_url: str
    width: int
    height: int
    markers: list[Marker]


class SearchRequest(ApiModel):
    query: str = Field(min_length=2, max_length=200)
    max_products: int = Field(default=20, ge=1, le=50)
    retailers: list[Retailer] = Field(default_factory=lambda: ["amazon"], min_length=1)


class SearchResponse(ApiModel):
    search_id: UUID
    products: list[Product]
    warnings: list[str] = Field(default_factory=list)


class ProductList(ApiModel):
    items: list[Product]


class ShadeList(ApiModel):
    items: list[Shade]


class ColorMapRequest(ApiModel):
    product_ids: list[UUID] | None = None


class HealthResponse(ApiModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    services: dict[str, bool]
