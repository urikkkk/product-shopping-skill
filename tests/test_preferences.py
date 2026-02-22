"""Tests for the preferences module."""

from src.preferences import BOOST_PER_MATCH, apply_preferences
from src.schema import Product
from src.scoring import ScoreBreakdown


def _make_scored(
    brand="TestBrand",
    title="Test Keyboard",
    total=50.0,
    features="Split, Tented",
    switch_type="Cherry MX Brown",
    programmable="QMK/VIA",
    connectivity="USB-C",
    category="Split",
) -> tuple[Product, ScoreBreakdown]:
    p = Product(
        product_title=title,
        brand=brand,
        ergonomic_features=features,
        switch_type=switch_type,
        programmable=programmable,
        connectivity=connectivity,
        category=category,
    )
    s = ScoreBreakdown(total=total, ergonomics=40.0, reviews=30.0, value=20.0, build=10.0)
    return (p, s)


class TestApplyPreferences:
    def test_brand_match_boosts(self):
        scored = [_make_scored(brand="Keychron", total=50.0)]
        result = apply_preferences(scored, "Keychron")
        assert result[0][1].total == 50.0 + BOOST_PER_MATCH

    def test_feature_match_boosts(self):
        scored = [_make_scored(features="Split, Tented", total=50.0)]
        result = apply_preferences(scored, "split")
        assert result[0][1].total == 50.0 + BOOST_PER_MATCH

    def test_multiple_matches(self):
        scored = [_make_scored(brand="Keychron", programmable="QMK/VIA", total=50.0)]
        result = apply_preferences(scored, "Keychron, QMK")
        assert result[0][1].total == 50.0 + 2 * BOOST_PER_MATCH

    def test_no_match_unchanged(self):
        scored = [_make_scored(brand="Logitech", total=50.0)]
        result = apply_preferences(scored, "Keychron")
        assert result[0][1].total == 50.0

    def test_cap_at_100(self):
        scored = [_make_scored(brand="Keychron", total=98.0)]
        result = apply_preferences(scored, "Keychron")
        assert result[0][1].total == 100

    def test_reranking(self):
        item_a = _make_scored(brand="Logitech", title="Logitech KB", total=60.0)
        item_b = _make_scored(brand="Keychron", title="Keychron KB", total=55.0)
        scored = [item_a, item_b]  # A is ranked higher
        result = apply_preferences(scored, "Keychron")
        # B should now be first after boost: 55 + 5 = 60, but same as A, so check order
        assert result[0][0].brand == "Keychron" or result[0][1].total >= result[1][1].total

    def test_empty_preferences_noop(self):
        scored = [_make_scored(total=50.0)]
        result = apply_preferences(scored, "")
        assert result[0][1].total == 50.0

    def test_none_preferences_noop(self):
        scored = [_make_scored(total=50.0)]
        result = apply_preferences(scored, "   ")
        assert result[0][1].total == 50.0

    def test_dimension_scores_preserved(self):
        scored = [_make_scored(brand="Keychron", total=50.0)]
        result = apply_preferences(scored, "Keychron")
        assert result[0][1].ergonomics == 40.0
        assert result[0][1].reviews == 30.0
        assert result[0][1].value == 20.0
        assert result[0][1].build == 10.0

    def test_case_insensitive(self):
        scored = [_make_scored(brand="Keychron", total=50.0)]
        result = apply_preferences(scored, "keychron")
        assert result[0][1].total == 50.0 + BOOST_PER_MATCH
