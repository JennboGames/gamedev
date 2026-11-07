import pytest

from src.errors.error_types import ConfigurationError, UpstreamError
from src.models.domain import SourceProduct
from src.services.retailer_search import MultiRetailerSearch, UnavailableSearch


def product(asin: str, retailer: str = "ulta") -> SourceProduct:
    return SourceProduct(
        asin=asin, title=asin, brand=None, detail_page_url=None, image_url=None, retailer=retailer
    )


class StubSearch:
    def __init__(self, products=None, error: Exception | None = None) -> None:
        self.products = products or []
        self.error = error
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, max_products: int) -> list[SourceProduct]:
        self.calls.append((query, max_products))
        if self.error:
            raise self.error
        return self.products

    def health_check(self) -> bool:
        return True


def test_merges_results_from_selected_retailers():
    router = MultiRetailerSearch(
        {
            "ulta": StubSearch([product("U1")]),
            "other": StubSearch([product("O1", "other")]),
        }
    )

    outcome = router.search("foundation", 5, ["ulta", "other"])

    assert [(p.retailer, p.asin) for p in outcome.products] == [("ulta", "U1"), ("other", "O1")]
    assert outcome.warnings == []


def test_only_selected_retailers_are_searched():
    ulta, other = StubSearch([product("U1")]), StubSearch([product("O1", "other")])
    MultiRetailerSearch({"ulta": ulta, "other": other}).search("foundation", 5, ["other"])

    assert ulta.calls == []
    assert other.calls == [("foundation", 5)]


def test_no_selected_retailer_searches_nothing():
    ulta = StubSearch([product("U1")])

    outcome = MultiRetailerSearch({"ulta": ulta}).search("foundation", 5)

    assert outcome.products == []
    assert ulta.calls == []


def test_failing_retailer_becomes_a_warning_when_others_succeed():
    router = MultiRetailerSearch(
        {
            "ulta": StubSearch([product("U1")]),
            "sephora": UnavailableSearch("Sephora blocks automated access"),
        }
    )

    outcome = router.search("foundation", 5, ["ulta", "sephora"])

    assert [p.asin for p in outcome.products] == ["U1"]
    assert outcome.warnings == ["Sephora: Sephora blocks automated access"]


def test_error_is_raised_when_every_selected_retailer_fails():
    router = MultiRetailerSearch({"ulta": StubSearch(error=ConfigurationError("no keys"))})

    with pytest.raises(ConfigurationError):
        router.search("foundation", 5, ["ulta"])


def test_unknown_retailer_is_reported_not_raised():
    outcome = MultiRetailerSearch({"ulta": StubSearch([product("U1")])}).search(
        "foundation", 5, ["ulta", "sephora"]
    )
    assert outcome.warnings == ["Sephora search is not available."]


def test_provider_upstream_failure_is_a_warning():
    router = MultiRetailerSearch(
        {
            "ulta": StubSearch([product("U1")]),
            "other": StubSearch(error=UpstreamError("down")),
        }
    )

    outcome = router.search("foundation", 5, ["ulta", "other"])

    assert [p.asin for p in outcome.products] == ["U1"]
    assert outcome.warnings == ["other: down"]


def test_health_needs_at_least_one_provider():
    assert MultiRetailerSearch({}).health_check() is False
    assert MultiRetailerSearch({"ulta": StubSearch()}).health_check() is True
