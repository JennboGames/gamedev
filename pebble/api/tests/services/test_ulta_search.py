import json

import pytest

from src.errors.error_types import UpstreamError
from src.services.ulta_search import LISTING_URL, UltaSearch, matches_query, parse_listing

DOUBLE_WEAR = (
    "https://www.ulta.com/p/double-wear-stay-in-place-longwear-matte-foundation-pimprod2057355"
)
FIT_ME = "https://www.ulta.com/p/fit-me-matte-poreless-liquid-foundation-xlsImpprod11861007"


def tile(url: str, brand: str, title: str, sku: str) -> str:
    return (
        f'<div class="pal-c-ProductCard"><a class="pal-c-Link" href="{url}?sku={sku}">'
        f'<span class="pal-c-Text__isScreenReader">{brand} {title}</span></a>'
        f'<div class="pal-c-ProductCardBody--brandName"><p class="pal-c-Text">{brand}</p></div>'
        f'<div class="pal-c-ProductCardBody--title"><p class="pal-c-Text">{title}</p></div></div>'
    )


LISTING_HTML = (
    "<html><body>"
    + tile(
        DOUBLE_WEAR,
        "Estée Lauder",
        "Double Wear Stay-in-Place Longwear Matte Foundation",
        "2651970",
    )
    + tile(
        DOUBLE_WEAR,
        "Estée Lauder",
        "Double Wear Stay-in-Place Longwear Matte Foundation",
        "2651971",
    )
    + tile(FIT_ME, "Maybelline", "Fit Me Matte + Poreless Liquid Foundation", "2510274")
    + "</body></html>"
)


def ld(data: dict) -> str:
    return f'<script type="application/ld+json">{json.dumps(data)}</script>'


def product_page(group_id: str, name: str, brand: str, variants: list[tuple[str, str]]) -> str:
    return (
        "<html><head>"
        + ld({"@context": "http://schema.org", "@type": "BreadcrumbList", "itemListElement": []})
        + ld(
            {
                "@type": "Product",
                "name": name,
                "brand": brand,
                "productID": group_id,
                "sku": variants[0][0],
            }
        )
        + ld(
            {
                "@type": "ProductGroup",
                "productGroupID": group_id,
                "hasVariant": [
                    {"@type": "Product", "sku": sku, "color": color, "name": f"{color} {name}"}
                    for sku, color in variants
                ],
            }
        )
        + "</head></html>"
    )


DOUBLE_WEAR_PAGE = product_page(
    "pimprod2057355",
    "Double Wear Stay-in-Place Longwear Matte Foundation",
    "Estée Lauder",
    [("2651970", "0N1 Alabaster"), ("2651971", "1C0 Shell"), ("2651972", "1C1 Cool Bone")],
)
FIT_ME_PAGE = product_page(
    "xlsImpprod11861007",
    "Fit Me Matte + Poreless Liquid Foundation",
    "Maybelline",
    [("2510274", "110 Porcelain")],
)


class RecordedPages:
    def __init__(self, pages: dict[str, tuple[int, str]]) -> None:
        self.pages = pages
        self.requests: list[tuple[str, dict[str, str]]] = []

    def __call__(self, url: str, headers: dict[str, str]) -> tuple[int, bytes]:
        self.requests.append((url, headers))
        status, body = self.pages[url]
        return status, body.encode("utf-8")


def make_search(pages: dict[str, tuple[int, str]], **kwargs) -> tuple[UltaSearch, RecordedPages]:
    transport = RecordedPages(pages)
    return UltaSearch(transport, sleep=lambda _s: None, min_interval_seconds=0, **kwargs), transport


def default_pages() -> dict[str, tuple[int, str]]:
    return {
        LISTING_URL: (200, LISTING_HTML),
        DOUBLE_WEAR: (200, DOUBLE_WEAR_PAGE),
        FIT_ME: (200, FIT_ME_PAGE),
    }


def test_parse_listing_dedupes_products_and_reads_brand_and_title():
    tiles = parse_listing(LISTING_HTML)

    assert tiles == [
        (DOUBLE_WEAR, "Estée Lauder", "Double Wear Stay-in-Place Longwear Matte Foundation"),
        (FIT_ME, "Maybelline", "Fit Me Matte + Poreless Liquid Foundation"),
    ]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("skin foundation", True),
        ("estee lauder", True),
        ("Estée Double Wear", True),
        ("maybelline", False),
    ],
)
def test_matches_query_ignores_generic_words_and_accents(query, expected):
    assert (
        matches_query(query, "Estée Lauder", "Double Wear Stay-in-Place Longwear Matte Foundation")
        is expected
    )


def test_search_returns_products_with_variant_shades():
    search, _ = make_search(default_pages())

    products = search.search("skin foundation", 5)

    assert [p.asin for p in products] == ["pimprod2057355", "xlsImpprod11861007"]
    double_wear = products[0]
    assert double_wear.retailer == "ulta"
    assert double_wear.brand == "Estée Lauder"
    assert double_wear.detail_page_url == DOUBLE_WEAR
    assert [s.name for s in double_wear.shades] == ["0N1 Alabaster", "1C0 Shell", "1C1 Cool Bone"]
    assert double_wear.shades[0].asin == "2651970"
    assert double_wear.shades[0].swatch_url == "https://media.ultainc.com/i/ulta/2651970_sw?w=80"


def test_search_filters_by_query_and_respects_max_products():
    search, transport = make_search(default_pages())

    assert [p.brand for p in search.search("maybelline", 5)] == ["Maybelline"]
    assert len(search.search("foundation", 1)) == 1
    assert all(url.startswith("https://www.ulta.com/") for url, _ in transport.requests)


def test_search_caps_shades_per_product():
    search, _ = make_search(default_pages(), max_shades=2)
    assert len(search.search("estee", 5)[0].shades) == 2


def test_requests_identify_the_client():
    search, transport = make_search(default_pages())
    search.search("maybelline", 5)
    assert "PebbleShadeBot" in transport.requests[0][1]["User-Agent"]


@pytest.mark.parametrize("status", [403, 429])
def test_blocked_requests_raise_an_upstream_error_without_retrying(status):
    search, transport = make_search({LISTING_URL: (status, "denied")})

    with pytest.raises(UpstreamError, match="blocked"):
        search.search("foundation", 5)
    assert len(transport.requests) == 1


def test_unexpected_status_raises_an_upstream_error():
    search, _ = make_search({LISTING_URL: (500, "oops")})
    with pytest.raises(UpstreamError, match="HTTP 500"):
        search.search("foundation", 5)


def test_product_page_without_structured_data_is_skipped():
    pages = default_pages()
    pages[FIT_ME] = (200, "<html></html>")
    search, _ = make_search(pages)

    assert [p.brand for p in search.search("foundation", 5)] == ["Estée Lauder"]
