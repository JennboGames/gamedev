"""PostgreSQL implementation of ShadeRepository.

Collection -> table mapping (migrations must create these):
  search -> searches, product -> products, shade -> shades,
  color map -> color_maps, color map marker -> color_map_markers
"""

import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from psycopg2.extras import RealDictCursor

from src.models.api import Product, ProductStatus, Shade
from src.models.domain import (
    CollectedProduct,
    ColorMapRecord,
    MapShade,
    PlottedMarker,
    ShadeExtraction,
)
from src.services.interfaces.connection_provider import DatabaseConnectionProvider

_PRODUCT_SELECT = """
    SELECT p.id, p.retailer, p.asin, p.title, p.brand, p.detail_page_url, p.image_url, p.status, p.created_at,
           (SELECT COUNT(*) FROM shades s WHERE s.product_id = p.id) AS shade_count,
           -- up to five hexes spread from lightest to darkest, for the collapsed product card
           (SELECT COALESCE(array_agg(picked.hex ORDER BY picked.lightness DESC), ARRAY[]::text[])
            FROM (
                SELECT DISTINCT ON (b.bucket) b.hex, b.lightness
                FROM (
                    SELECT s2.hex, s2.lightness, ntile(5) OVER (ORDER BY s2.lightness DESC) AS bucket
                    FROM shades s2
                    WHERE s2.product_id = p.id AND s2.hex IS NOT NULL
                ) b
                ORDER BY b.bucket, b.lightness DESC
            ) picked) AS sample_hexes
    FROM products p
"""

_SHADE_COLUMNS = "id, product_id, asin, name, swatch_url, hex, hue, lightness, status, error"


def _product_status(extractions: list[ShadeExtraction]) -> ProductStatus:
    return "collected" if all(e.status == "extracted" for e in extractions) else "partial"


def _to_product(row: dict[str, Any]) -> Product:
    return Product(
        id=row["id"],
        retailer=row["retailer"],
        asin=row["asin"],
        title=row["title"],
        brand=row["brand"],
        detail_page_url=row["detail_page_url"],
        image_url=row["image_url"],
        shade_count=row["shade_count"],
        sample_hexes=list(row["sample_hexes"] or []),
        status=row["status"],
        created_at=row["created_at"],
    )


def _to_shade(row: dict[str, Any]) -> Shade:
    return Shade(
        id=row["id"],
        product_id=row["product_id"],
        asin=row["asin"],
        name=row["name"],
        swatch_url=row["swatch_url"],
        hex=row["hex"],
        hue=row["hue"],
        lightness=row["lightness"],
        status=row["status"],
        error=row["error"],
    )


def _to_map_shade(row: dict[str, Any]) -> MapShade:
    return MapShade(
        shade_id=str(row["shade_id"]),
        product_id=str(row["product_id"]),
        shade_name=row["shade_name"],
        product_title=row["product_title"],
        hex=row["hex"],
        hue=float(row["hue"]),
        lightness=float(row["lightness"]),
    )


class PostgresShadeRepository:
    def __init__(self, provider: DatabaseConnectionProvider) -> None:
        self._provider = provider

    @contextmanager
    def _transaction(self) -> Iterator[Any]:
        """One connection, one transaction: commits on success, rolls back on any exception."""
        connection = self._provider.connect()
        try:
            with connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    yield cursor
        finally:
            connection.close()

    def save_search(
        self, query: str, products: list[CollectedProduct]
    ) -> tuple[str, list[Product]]:
        search_id = str(uuid.uuid4())
        with self._transaction() as cur:
            cur.execute("INSERT INTO searches (id, query) VALUES (%s, %s)", (search_id, query))

            product_ids: list[str] = []
            for collected in products:
                product = collected.product
                status = _product_status([c.extraction for c in collected.shades])
                cur.execute(
                    """
                    INSERT INTO products (id, retailer, asin, title, brand, detail_page_url, image_url, status, search_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (retailer, asin) DO UPDATE SET
                        title = EXCLUDED.title, brand = EXCLUDED.brand,
                        detail_page_url = EXCLUDED.detail_page_url, image_url = EXCLUDED.image_url,
                        status = EXCLUDED.status, search_id = EXCLUDED.search_id, updated_at = now()
                    RETURNING id
                    """,
                    (
                        str(uuid.uuid4()),
                        product.retailer,
                        product.asin,
                        product.title,
                        product.brand,
                        product.detail_page_url,
                        product.image_url,
                        status,
                        search_id,
                    ),
                )
                product_id = str(cur.fetchone()["id"])
                product_ids.append(product_id)

                for item in collected.shades:
                    extraction = item.extraction
                    cur.execute(
                        """
                        INSERT INTO shades (id, product_id, asin, name, swatch_url, swatch_blob_name,
                                            hex, hue, lightness, status, error)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (product_id, asin) DO UPDATE SET
                            name = EXCLUDED.name, swatch_url = EXCLUDED.swatch_url,
                            swatch_blob_name = EXCLUDED.swatch_blob_name, hex = EXCLUDED.hex,
                            hue = EXCLUDED.hue, lightness = EXCLUDED.lightness,
                            status = EXCLUDED.status, error = EXCLUDED.error, updated_at = now()
                        """,
                        (
                            str(uuid.uuid4()),
                            product_id,
                            item.shade.asin,
                            item.shade.name,
                            item.shade.swatch_url,
                            extraction.swatch_blob_name,
                            extraction.hex,
                            extraction.hue,
                            extraction.lightness,
                            extraction.status,
                            extraction.error,
                        ),
                    )

            saved: dict[str, Product] = {}
            if product_ids:
                cur.execute(_PRODUCT_SELECT + " WHERE p.id = ANY(%s::uuid[])", (product_ids,))
                saved = {str(row["id"]): _to_product(row) for row in cur.fetchall()}

        return search_id, [saved[pid] for pid in product_ids if pid in saved]

    def list_products(self) -> list[Product]:
        with self._transaction() as cur:
            cur.execute(_PRODUCT_SELECT + " ORDER BY p.created_at DESC, p.title")
            return [_to_product(row) for row in cur.fetchall()]

    def get_product(self, product_id: str) -> Product | None:
        with self._transaction() as cur:
            cur.execute(_PRODUCT_SELECT + " WHERE p.id = %s", (product_id,))
            row = cur.fetchone()
            return _to_product(row) if row else None

    def list_shades(self, product_id: str) -> list[Shade]:
        with self._transaction() as cur:
            cur.execute(
                f"SELECT {_SHADE_COLUMNS} FROM shades WHERE product_id = %s ORDER BY name",
                (product_id,),
            )
            return [_to_shade(row) for row in cur.fetchall()]

    def get_shade(self, shade_id: str) -> Shade | None:
        with self._transaction() as cur:
            cur.execute(f"SELECT {_SHADE_COLUMNS} FROM shades WHERE id = %s", (shade_id,))
            row = cur.fetchone()
            return _to_shade(row) if row else None

    def update_shade_extraction(self, shade_id: str, extraction: ShadeExtraction) -> Shade | None:
        with self._transaction() as cur:
            cur.execute(
                f"""
                UPDATE shades SET status = %s, hex = %s, hue = %s, lightness = %s,
                    swatch_blob_name = COALESCE(%s, swatch_blob_name), error = %s, updated_at = now()
                WHERE id = %s
                RETURNING {_SHADE_COLUMNS}
                """,
                (
                    extraction.status,
                    extraction.hex,
                    extraction.hue,
                    extraction.lightness,
                    extraction.swatch_blob_name,
                    extraction.error,
                    shade_id,
                ),
            )
            row = cur.fetchone()
            if row is None:
                return None
            cur.execute(
                """
                UPDATE products SET updated_at = now(), status = CASE
                    WHEN EXISTS (SELECT 1 FROM shades WHERE product_id = products.id AND status <> 'extracted')
                    THEN 'partial' ELSE 'collected' END
                WHERE id = %s
                """,
                (row["product_id"],),
            )
            return _to_shade(row)

    def list_map_shades(self, product_ids: list[str] | None) -> list[MapShade]:
        sql = """
            SELECT s.id AS shade_id, s.product_id, s.name AS shade_name, p.title AS product_title,
                   s.hex, s.hue, s.lightness
            FROM shades s JOIN products p ON p.id = s.product_id
            WHERE s.hex IS NOT NULL
        """
        params: tuple[Any, ...] = ()
        if product_ids:
            sql += " AND s.product_id = ANY(%s::uuid[])"
            params = (product_ids,)
        sql += " ORDER BY p.title, s.name"
        with self._transaction() as cur:
            cur.execute(sql, params)
            return [_to_map_shade(row) for row in cur.fetchall()]

    def save_color_map(self, record: ColorMapRecord) -> None:
        with self._transaction() as cur:
            cur.execute(
                "INSERT INTO color_maps (id, blob_name, width, height) VALUES (%s, %s, %s, %s)",
                (record.id, record.blob_name, record.width, record.height),
            )
            cur.executemany(
                """
                INSERT INTO color_map_markers (id, color_map_id, shade_id, x, y, hex, hue, lightness)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        str(uuid.uuid4()),
                        record.id,
                        m.shade.shade_id,
                        m.x,
                        m.y,
                        m.shade.hex,
                        m.shade.hue,
                        m.shade.lightness,
                    )
                    for m in record.markers
                ],
            )

    def get_latest_color_map(self) -> ColorMapRecord | None:
        with self._transaction() as cur:
            cur.execute(
                "SELECT id, blob_name, width, height FROM color_maps ORDER BY created_at DESC LIMIT 1"
            )
            header = cur.fetchone()
            if header is None:
                return None
            cur.execute(
                """
                SELECT m.x, m.y, m.hex, m.hue, m.lightness, s.id AS shade_id, s.product_id,
                       s.name AS shade_name, p.title AS product_title
                FROM color_map_markers m
                JOIN shades s ON s.id = m.shade_id
                JOIN products p ON p.id = s.product_id
                WHERE m.color_map_id = %s
                ORDER BY p.title, s.name
                """,
                (header["id"],),
            )
            markers = tuple(
                PlottedMarker(_to_map_shade(row), float(row["x"]), float(row["y"]))
                for row in cur.fetchall()
            )
            return ColorMapRecord(
                id=str(header["id"]),
                blob_name=header["blob_name"],
                width=header["width"],
                height=header["height"],
                markers=markers,
            )

    def health_check(self) -> bool:
        try:
            with self._transaction() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception:  # noqa: BLE001
            return False
