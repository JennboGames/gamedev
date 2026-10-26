"""In-memory ShadeRepository for tests. Mirrors the Postgres behavior that handlers rely on."""

import uuid
from datetime import datetime, timezone

from src.models.api import Product, Shade
from src.models.domain import CollectedProduct, ColorMapRecord, MapShade, ShadeExtraction


class InMemoryShadeRepository:
    def __init__(self) -> None:
        self.products: dict[str, Product] = {}
        self.product_asins: dict[str, tuple[str, str]] = {}
        self.shades: dict[str, Shade] = {}
        self.color_maps: list[ColorMapRecord] = []
        self.healthy = True

    def save_search(
        self, query: str, products: list[CollectedProduct]
    ) -> tuple[str, list[Product]]:
        saved: list[Product] = []
        for collected in products:
            statuses = [c.extraction.status for c in collected.shades]
            key = (collected.product.retailer, collected.product.asin)
            product_id = next(
                (pid for pid, existing in self.product_asins.items() if existing == key),
                str(uuid.uuid4()),
            )
            self.product_asins[product_id] = key
            for item in collected.shades:
                shade_id = next(
                    (
                        sid
                        for sid, s in self.shades.items()
                        if str(s.product_id) == product_id and s.asin == item.shade.asin
                    ),
                    str(uuid.uuid4()),
                )
                self.shades[shade_id] = Shade(
                    id=shade_id,
                    product_id=product_id,
                    asin=item.shade.asin,
                    name=item.shade.name,
                    swatch_url=item.shade.swatch_url,
                    hex=item.extraction.hex,
                    hue=item.extraction.hue,
                    lightness=item.extraction.lightness,
                    status=item.extraction.status,
                    error=item.extraction.error,
                )
            self.products[product_id] = Product(
                id=product_id,
                retailer=collected.product.retailer,
                asin=collected.product.asin,
                title=collected.product.title,
                brand=collected.product.brand,
                detail_page_url=collected.product.detail_page_url,
                image_url=collected.product.image_url,
                shade_count=len(collected.shades),
                status="collected" if all(s == "extracted" for s in statuses) else "partial",
                created_at=datetime.now(timezone.utc),
            )
            saved.append(self.products[product_id])
        return str(uuid.uuid4()), saved

    def list_products(self) -> list[Product]:
        return list(self.products.values())

    def get_product(self, product_id: str) -> Product | None:
        return self.products.get(product_id)

    def list_shades(self, product_id: str) -> list[Shade]:
        return sorted(
            (s for s in self.shades.values() if str(s.product_id) == product_id),
            key=lambda s: s.name,
        )

    def get_shade(self, shade_id: str) -> Shade | None:
        return self.shades.get(shade_id)

    def update_shade_extraction(self, shade_id: str, extraction: ShadeExtraction) -> Shade | None:
        current = self.shades.get(shade_id)
        if current is None:
            return None
        updated = current.model_copy(
            update={
                "hex": extraction.hex,
                "hue": extraction.hue,
                "lightness": extraction.lightness,
                "status": extraction.status,
                "error": extraction.error,
            }
        )
        self.shades[shade_id] = updated
        return updated

    def list_map_shades(self, product_ids: list[str] | None) -> list[MapShade]:
        result = []
        for shade in self.shades.values():
            product_id = str(shade.product_id)
            if shade.hex is None or (product_ids and product_id not in product_ids):
                continue
            result.append(
                MapShade(
                    shade_id=str(shade.id),
                    product_id=product_id,
                    shade_name=shade.name,
                    product_title=self.products[product_id].title,
                    hex=shade.hex,
                    hue=shade.hue or 0.0,
                    lightness=shade.lightness or 0.0,
                )
            )
        return result

    def save_color_map(self, record: ColorMapRecord) -> None:
        self.color_maps.append(record)

    def get_latest_color_map(self) -> ColorMapRecord | None:
        return self.color_maps[-1] if self.color_maps else None

    def health_check(self) -> bool:
        return self.healthy
