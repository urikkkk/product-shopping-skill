"""Tests for the scoring engine."""

from src.schema import Product
from src.scoring import (
    ScoreBreakdown,
    rank_products,
    score_build,
    score_ergonomics,
    score_product,
    score_reviews,
    score_value,
)


def _make_product(**kwargs) -> Product:
    defaults = {
        "product_title": "Test Keyboard",
        "brand": "TestBrand",
        "price_usd": 200,
        "rating_avg": 4.5,
        "rating_count": 500,
        "switch_type": "Cherry MX Brown",
        "switch_brand": "Cherry",
        "hot_swappable": True,
        "programmable": "QMK/VIA",
        "connectivity": "Bluetooth + USB-C",
        "ergonomic_features": "Split, Tented, Thumb clusters",
    }
    defaults.update(kwargs)
    return Product(**defaults)


class TestScoreErgonomics:
    def test_split_scores(self):
        p = _make_product(ergonomic_features="Split")
        assert score_ergonomics(p) == 30

    def test_split_tented(self):
        p = _make_product(ergonomic_features="Split, Tented")
        assert score_ergonomics(p) == 50

    def test_full_ergo(self):
        p = _make_product(
            ergonomic_features="Split, Tented, Contoured keywells, Thumb clusters"
        )
        assert score_ergonomics(p) == 75

    def test_no_features(self):
        p = _make_product(ergonomic_features="Standard layout")
        assert score_ergonomics(p) == 0

    def test_caps_at_100(self):
        p = _make_product(
            ergonomic_features="Split, Tented, Tilt, Wrist rest, Contoured, Thumb, Ortholinear"
        )
        assert score_ergonomics(p) == 100


class TestScoreReviews:
    def test_high_rated_many_reviews(self):
        p = _make_product(rating_avg=4.8, rating_count=5000)
        score = score_reviews(p)
        assert score > 90

    def test_no_reviews(self):
        p = _make_product(rating_avg=0, rating_count=0)
        assert score_reviews(p) == 0


class TestScoreValue:
    def test_cheap_product(self):
        p = _make_product(price_usd=50)
        assert score_value(p) == 90

    def test_expensive_product(self):
        p = _make_product(price_usd=500)
        assert score_value(p) == 0

    def test_free(self):
        p = _make_product(price_usd=0)
        assert score_value(p) == 100


class TestScoreBuild:
    def test_membrane_penalty(self):
        p = _make_product(switch_type="Membrane", hot_swappable=False, programmable="No",
                          connectivity="USB", switch_brand="")
        assert score_build(p) == 0  # max(0, -30)

    def test_full_featured(self):
        p = _make_product()
        score = score_build(p)
        assert score >= 70  # hot-swap(25) + QMK(30) + BT(15) + Cherry(15) = 85


class TestScoreProduct:
    def test_returns_breakdown(self):
        p = _make_product()
        result = score_product(p)
        assert isinstance(result, ScoreBreakdown)
        assert result.total > 0


class TestRankProducts:
    def test_returns_top_n(self):
        products = [_make_product(price_usd=i * 50) for i in range(1, 6)]
        ranked = rank_products(products, top_n=3, deduplicate=False)
        assert len(ranked) == 3

    def test_sorted_by_score(self):
        p1 = _make_product(product_title="Cheap", price_usd=50)
        p2 = _make_product(product_title="Expensive", price_usd=500)
        ranked = rank_products([p1, p2], top_n=2, deduplicate=False)
        assert ranked[0][1].total >= ranked[1][1].total

    def test_deduplication(self):
        p1 = _make_product(product_title="Same", brand="B", price_usd=100, source_site="Amazon")
        p2 = _make_product(product_title="Same", brand="B", price_usd=120, source_site="Walmart")
        ranked = rank_products([p1, p2], top_n=10, deduplicate=True)
        assert len(ranked) == 1
        assert ranked[0][0].price_usd == 100  # Keeps cheaper
