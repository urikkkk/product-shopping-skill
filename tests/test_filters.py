"""Tests for the filters module."""

from src.filters import apply_filters
from src.schema import Product


def _make_product(**kwargs) -> Product:
    defaults = {
        "product_title": "Test Keyboard",
        "brand": "TestBrand",
        "price_usd": 200,
        "rating_avg": 4.5,
        "rating_count": 500,
        "connectivity": "Bluetooth + USB-C",
        "layout_size": "Split 75%",
        "category": "Split",
    }
    defaults.update(kwargs)
    return Product(**defaults)


class TestBudgetFilter:
    def test_filters_over_budget(self):
        products = [_make_product(price_usd=100), _make_product(price_usd=300)]
        result = apply_filters(products, budget=200)
        assert len(result) == 1
        assert result[0].price_usd == 100

    def test_includes_at_budget(self):
        products = [_make_product(price_usd=200)]
        result = apply_filters(products, budget=200)
        assert len(result) == 1

    def test_no_budget(self):
        products = [_make_product(price_usd=1000)]
        result = apply_filters(products, budget=None)
        assert len(result) == 1


class TestWirelessFilter:
    def test_wireless_yes(self):
        products = [
            _make_product(connectivity="Bluetooth + USB-C"),
            _make_product(connectivity="USB only"),
        ]
        result = apply_filters(products, wireless="yes")
        assert len(result) == 1
        assert "Bluetooth" in result[0].connectivity

    def test_wireless_yes_2_4ghz(self):
        products = [_make_product(connectivity="2.4GHz + USB-C")]
        result = apply_filters(products, wireless="yes")
        assert len(result) == 1

    def test_wireless_no(self):
        products = [
            _make_product(connectivity="Bluetooth + USB-C"),
            _make_product(connectivity="USB only"),
        ]
        result = apply_filters(products, wireless="no")
        assert len(result) == 1
        assert "USB only" in result[0].connectivity

    def test_wireless_none(self):
        products = [
            _make_product(connectivity="Bluetooth"),
            _make_product(connectivity="USB"),
        ]
        result = apply_filters(products, wireless=None)
        assert len(result) == 2


class TestLayoutFilter:
    def test_layout_match_in_layout_size(self):
        products = [
            _make_product(layout_size="Split 75%", category="Mechanical"),
            _make_product(layout_size="Standard Full", category="Standard"),
        ]
        result = apply_filters(products, layout="split")
        assert len(result) == 1

    def test_layout_match_in_category(self):
        products = [
            _make_product(layout_size="Standard", category="Alice"),
        ]
        result = apply_filters(products, layout="alice")
        assert len(result) == 1

    def test_layout_case_insensitive(self):
        products = [_make_product(layout_size="Split 75%")]
        result = apply_filters(products, layout="SPLIT")
        assert len(result) == 1


class TestMinRatingCount:
    def test_filters_low_count(self):
        products = [
            _make_product(rating_count=50),
            _make_product(rating_count=200),
        ]
        result = apply_filters(products, min_rating_count=100)
        assert len(result) == 1
        assert result[0].rating_count == 200

    def test_zero_min(self):
        products = [_make_product(rating_count=0)]
        result = apply_filters(products, min_rating_count=0)
        assert len(result) == 1


class TestCombinedFilters:
    def test_budget_and_wireless(self):
        products = [
            _make_product(price_usd=150, connectivity="Bluetooth"),
            _make_product(price_usd=300, connectivity="Bluetooth"),
            _make_product(price_usd=100, connectivity="USB"),
        ]
        result = apply_filters(products, budget=200, wireless="yes")
        assert len(result) == 1
        assert result[0].price_usd == 150

    def test_no_filters_passthrough(self):
        products = [_make_product(), _make_product()]
        result = apply_filters(products)
        assert len(result) == 2
