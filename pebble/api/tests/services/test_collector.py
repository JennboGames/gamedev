import pytest

from src.errors.error_types import NotFoundError, UpstreamError
from tests.conftest import BROKEN_URL, IVORY_URL


def test_collect_extracts_hex_and_stores_swatches(services):
    search_id, products, warnings = services.collector().collect("skin foundation", 20)

    assert search_id
    assert warnings == []
    assert len(products) == 1
    shades = {s.name: s for s in services.repository.list_shades(str(products[0].id))}
    assert shades["1N1 Ivory Nude"].hex == "#F1D2B5"
    assert shades["1N1 Ivory Nude"].status == "extracted"
    assert ("swatches", "amazon/B0GQVP8RLD/S1.png") in services.blob_store.objects


def test_collect_records_failed_swatch_without_failing_the_search(services):
    _, products, _ = services.collector().collect("skin foundation", 20)

    failed = next(
        s for s in services.repository.list_shades(str(products[0].id)) if s.name == "3C2 Pebble"
    )
    assert failed.status == "failed"
    assert failed.hex is None
    assert products[0].status == "partial"


def test_collect_passes_query_limit_and_retailers_to_search(services):
    services.collector().collect("skin foundation", 5, ["amazon", "ulta"])
    assert services.product_search.calls == [("skin foundation", 5, ("amazon", "ulta"))]


def test_collect_returns_retailer_warnings(services):
    services.product_search.warnings = ["Sephora: blocked"]
    _, _, warnings = services.collector().collect("skin foundation", 5)
    assert warnings == ["Sephora: blocked"]


def test_reextract_updates_shade(services):
    _, products, _ = services.collector().collect("skin foundation", 20)
    failed = next(
        s for s in services.repository.list_shades(str(products[0].id)) if s.name == "3C2 Pebble"
    )

    services.image_fetcher.images[BROKEN_URL] = services.image_fetcher.images[IVORY_URL]
    updated = services.collector().reextract_shade(str(failed.id))

    assert updated.hex == "#F1D2B5"
    assert updated.status == "extracted"


def test_reextract_failure_keeps_previous_hex(services):
    _, products, _ = services.collector().collect("skin foundation", 20)
    good = next(
        s
        for s in services.repository.list_shades(str(products[0].id))
        if s.name == "1N1 Ivory Nude"
    )

    del services.image_fetcher.images[IVORY_URL]
    with pytest.raises(UpstreamError):
        services.collector().reextract_shade(str(good.id))

    assert services.repository.get_shade(str(good.id)).hex == "#F1D2B5"


def test_reextract_unknown_shade_is_not_found(services):
    with pytest.raises(NotFoundError):
        services.collector().reextract_shade("00000000-0000-0000-0000-000000000000")


def test_generate_color_map_plots_only_shades_with_hex(services):
    services.collector().collect("skin foundation", 20)

    color_map = services.color_maps().generate(None)

    assert len(color_map.markers) == 2
    assert color_map.image_url.startswith("https://blob.test/colormaps/")
    lighter, darker = sorted(color_map.markers, key=lambda m: m.y)
    assert lighter.shade_name == "1N1 Ivory Nude"
    assert darker.shade_name == "6N2 Truffle"
    assert len(services.blob_store.objects) >= 3  # two swatches plus the map image


def test_generate_color_map_without_shades_is_not_found(services):
    with pytest.raises(NotFoundError):
        services.color_maps().generate(None)


def test_latest_color_map_returns_generated_map(services):
    services.collector().collect("skin foundation", 20)
    generated = services.color_maps().generate(None)

    latest = services.color_maps().latest()

    assert latest.image_url == generated.image_url
    assert len(latest.markers) == len(generated.markers)


def test_latest_color_map_missing_is_not_found(services):
    with pytest.raises(NotFoundError):
        services.color_maps().latest()
