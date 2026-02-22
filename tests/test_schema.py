"""Tests for schema normalization utilities."""

from src.schema import Product, normalize_bool, normalize_price, normalize_rating


class TestNormalizePrice:
    def test_float_passthrough(self):
        assert normalize_price(129.99) == 129.99

    def test_int_passthrough(self):
        assert normalize_price(100) == 100.0

    def test_dollar_string(self):
        assert normalize_price("$129.99") == 129.99

    def test_comma_string(self):
        assert normalize_price("$1,299.00") == 1299.0

    def test_none(self):
        assert normalize_price(None) == 0.0

    def test_empty_string(self):
        assert normalize_price("") == 0.0

    def test_garbage(self):
        assert normalize_price("free") == 0.0


class TestNormalizeRating:
    def test_float_passthrough(self):
        assert normalize_rating(4.5) == 4.5

    def test_string(self):
        assert normalize_rating("4.5") == 4.5

    def test_out_of_format(self):
        assert normalize_rating("4.5 out of 5") == 4.5

    def test_none(self):
        assert normalize_rating(None) == 0.0


class TestNormalizeBool:
    def test_true_string(self):
        assert normalize_bool("true") is True
        assert normalize_bool("True") is True
        assert normalize_bool("yes") is True
        assert normalize_bool("1") is True

    def test_false_string(self):
        assert normalize_bool("false") is False
        assert normalize_bool("no") is False
        assert normalize_bool("0") is False

    def test_bool_passthrough(self):
        assert normalize_bool(True) is True
        assert normalize_bool(False) is False

    def test_none(self):
        assert normalize_bool(None) is False


class TestProduct:
    def test_field_names(self):
        names = Product.field_names()
        assert "source_site" in names
        assert "product_title" in names
        assert "extra" not in names

    def test_to_dict(self):
        p = Product(product_title="Test", price_usd=99.0, extra={"foo": "bar"})
        d = p.to_dict()
        assert d["product_title"] == "Test"
        assert d["price_usd"] == 99.0
        assert "extra" not in d
