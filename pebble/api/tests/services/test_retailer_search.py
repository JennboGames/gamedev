import pytest

from src.errors.error_types import ConfigurationError, UpstreamError
from src.models.domain import AmazonProduct
from src.services.retailer_search import MultiRetailerSearch, UnavailableSearch


def product(asin: str, retailer: str = "amazon") -> AmazonProduct:
    return AmazonProduct(
        asin=asin, title=asin, brand=None, detail_page_url=None, image_url=None, retailer=retailer
    )


class StubSearch:
    def __init__(self, products=None, error: Exception | None = None) -> None:
        self.products = products or []
        self.error = error
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, max_products: int) -> list[AmazonProduct]:
        self.calls.append((query, max_products))
        if self.error:
            raise self.error
        return self.products

    def health_check(self) -> bool:
        return True


def test_merges_results_from_selected_retailers():
    router = MultiRetailerSearch(
        {
            "amazon": StubSearch([product("A1")]),
            "ulta": StubSearch([product("U1", "ulta")]),
        }
    )

    outcome = router.search("foundation", 5, ["amazon", "ulta"])

    assert [(p.retailer, p.asin) for p in outcome.products] == [("amazon", "A1"), ("ulta", "U1")]
    assert outcome.warnings == []


def test_only_selected_retailers_are_searched():
    amazon, ulta = StubSearch([product("A1")]), StubSearch([product("U1", "ulta")])
    MultiRetailerSearch({"amazon": amazon, "ulta": ulta}).search("foundation", 5, ["ulta"])

    assert amazon.calls == []
    assert ulta.calls == [("foundation", 5)]


def test_failing_retailer_becomes_a_warning_when_others_succeed():
    router = MultiRetailerSearch(
        {
            "amazon": StubSearch([product("A1")]),
            "sephora": UnavailableSearch("Sephora blocks automated access"),
        }
    )

    outcome = router.search("foundation", 5, ["amazon", "sephora"])

    assert [p.asin for p in outcome.products] == ["A1"]
    assert outcome.warnings == ["Sephora: Sephora blocks automated access"]


def test_error_is_raised_when_every_selected_retailer_fails():
    router = MultiRetailerSearch({"amazon": StubSearch(error=ConfigurationError("no keys"))})

    with pytest.raises(ConfigurationError):
        router.search("foundation", 5, ["amazon"])


def test_unknown_retailer_is_reported_not_raised():
    outcome = MultiRetailerSearch({"amazon": StubSearch([product("A1")])}).search(
        "foundation", 5, ["amazon", "ulta"]
    )
    assert outcome.warnings == ["Ulta search is not available."]


def test_pinned_products_are_added_when_amazon_is_not_selected():
    router = MultiRetailerSearch(
        {"ulta": StubSearch([product("U1", "ulta")])}, pinned=lambda: [product("PIN")]
    )

    outcome = router.search("foundation", 5, ["ulta"])

    assert [p.asin for p in outcome.products] == ["PIN", "U1"]


def test_pinned_products_are_not_fetched_twice_when_amazon_is_selected():
    calls: list[int] = []
    router = MultiRetailerSearch(
        {"amazon": StubSearch([product("PIN"), product("A1")])},
        pinned=lambda: calls.append(1) or [product("PIN")],
    )

    outcome = router.search("foundation", 5, ["amazon"])

    assert calls == []
    assert [p.asin for p in outcome.products] == ["PIN", "A1"]


def test_pinned_failure_is_a_warning():
    def failing() -> list[AmazonProduct]:
        raise UpstreamError("Amazon is down")

    router = MultiRetailerSearch({"ulta": StubSearch([product("U1", "ulta")])}, pinned=failing)

    outcome = router.search("foundation", 5, ["ulta"])

    assert [p.asin for p in outcome.products] == ["U1"]
    assert outcome.warnings == ["Amazon: Amazon is down"]
