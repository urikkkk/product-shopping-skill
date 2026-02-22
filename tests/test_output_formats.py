"""Tests for text and JSON output formatters."""

import json

from src.enrichment.reviews import ProReview
from src.output_formats import format_json, format_text
from src.schema import Product
from src.scoring import ScoreBreakdown


def _make_ranked():
    """Create sample ranked results for testing."""
    p1 = Product(
        product_title="Keychron Q10 Pro",
        brand="Keychron",
        price_usd=219,
        rating_avg=4.5,
        rating_count=340,
        source_site="Amazon",
        layout_size="Alice 75%",
        switch_type="Gateron Brown",
        connectivity="Bluetooth + USB-C",
        hot_swappable=True,
        programmable="QMK/VIA",
        ergonomic_features="Alice curved split",
        category="Alice",
        product_url="https://example.com/q10",
    )
    s1 = ScoreBreakdown(total=72.5, dimensions={"ergonomics": 30.0, "reviews": 63.0, "value": 56.2, "build": 85.0})

    p2 = Product(
        product_title="Logitech Ergo K860",
        brand="Logitech",
        price_usd=129,
        rating_avg=4.4,
        rating_count=12500,
        source_site="Best Buy",
        layout_size="Wave Split Full",
        switch_type="Membrane",
        connectivity="Bluetooth",
        ergonomic_features="Split wave, Tented",
        category="Wave/Ergo",
        product_url="https://example.com/k860",
    )
    s2 = ScoreBreakdown(total=55.3, dimensions={"ergonomics": 50.0, "reviews": 91.6, "value": 74.2, "build": 0.0})

    return [(p1, s1), (p2, s2)]


def _make_reviews():
    return {
        "Keychron Q10 Pro": [
            ProReview(source="TechGearLab", verdict="Best mainstream ergo mech", pros="Great value"),
        ],
        "Logitech Ergo K860": [],
    }


def _make_metadata():
    return {"query": "ergonomic keyboard", "mode": "seed", "budget": 300}


class TestFormatText:
    def test_returns_string(self):
        text = format_text(_make_ranked(), _make_reviews(), _make_metadata())
        assert isinstance(text, str)

    def test_contains_markdown_table(self):
        text = format_text(_make_ranked(), _make_reviews(), _make_metadata())
        assert "| # |" in text
        assert "|---|" in text

    def test_contains_products(self):
        text = format_text(_make_ranked(), _make_reviews(), _make_metadata())
        assert "Keychron Q10 Pro" in text
        assert "Logitech Ergo K860" in text

    def test_contains_score_breakdown(self):
        text = format_text(_make_ranked(), _make_reviews(), _make_metadata())
        assert "72.5" in text
        assert "30.0" in text  # ergonomics for Q10

    def test_contains_metadata(self):
        text = format_text(_make_ranked(), _make_reviews(), _make_metadata())
        assert "ergonomic keyboard" in text
        assert "seed" in text

    def test_contains_scoring_weights(self):
        text = format_text(_make_ranked(), _make_reviews(), _make_metadata())
        assert "40%" in text
        assert "20%" in text

    def test_contains_pro_reviews(self):
        text = format_text(_make_ranked(), _make_reviews(), _make_metadata())
        assert "TechGearLab" in text
        assert "Best mainstream ergo mech" in text

    def test_no_reviews_section_when_empty(self):
        text = format_text(_make_ranked(), {}, _make_metadata())
        assert "### Pro Reviews" not in text

    def test_no_metadata(self):
        text = format_text(_make_ranked(), {}, None)
        assert "Results: 2" in text


class TestFormatJson:
    def test_returns_valid_json(self):
        raw = format_json(_make_ranked(), _make_reviews(), _make_metadata())
        data = json.loads(raw)
        assert isinstance(data, dict)

    def test_has_metadata_and_results(self):
        data = json.loads(format_json(_make_ranked(), _make_reviews(), _make_metadata()))
        assert "metadata" in data
        assert "results" in data

    def test_result_count(self):
        data = json.loads(format_json(_make_ranked(), _make_reviews(), _make_metadata()))
        assert len(data["results"]) == 2

    def test_results_have_scores(self):
        data = json.loads(format_json(_make_ranked(), _make_reviews(), _make_metadata()))
        first = data["results"][0]
        assert "scores" in first
        assert first["scores"]["total"] == 72.5
        assert first["scores"]["ergonomics"] == 30.0
        assert first["scores"]["reviews"] == 63.0
        assert first["scores"]["value"] == 56.2
        assert first["scores"]["build"] == 85.0

    def test_results_have_rank(self):
        data = json.loads(format_json(_make_ranked(), _make_reviews(), _make_metadata()))
        assert data["results"][0]["rank"] == 1
        assert data["results"][1]["rank"] == 2

    def test_metadata_has_scoring_weights(self):
        data = json.loads(format_json(_make_ranked(), _make_reviews(), _make_metadata()))
        weights = data["metadata"]["scoring_weights"]
        assert weights["ergonomics"] == 0.4
        assert weights["reviews"] == 0.2
        assert weights["value"] == 0.2
        assert weights["build"] == 0.2

    def test_metadata_has_query(self):
        data = json.loads(format_json(_make_ranked(), _make_reviews(), _make_metadata()))
        assert data["metadata"]["query"] == "ergonomic keyboard"

    def test_results_have_pro_reviews(self):
        data = json.loads(format_json(_make_ranked(), _make_reviews(), _make_metadata()))
        first = data["results"][0]
        assert len(first["pro_reviews"]) == 1
        assert first["pro_reviews"][0]["source"] == "TechGearLab"

    def test_no_metadata(self):
        data = json.loads(format_json(_make_ranked(), {}, None))
        assert data["metadata"]["result_count"] == 2
