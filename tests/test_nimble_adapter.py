"""Tests for the Nimble WSA adapter."""

from unittest.mock import MagicMock, patch

import httpx

from src.adapters.nimble_adapter import NimbleAdapter
from src.schema import Product


# -- Sample API responses for mocking --

MOCK_AGENTS_RESPONSE = [
    {
        "name": "amazon_serp",
        "vertical": "Ecommerce",
        "entity_type": "SERP",
        "data_source": "Amazon",
        "is_localization_supported": True,
        "input_properties": [
            {"name": "keyword", "is_required": True},
            {"name": "zip_code", "is_required": False},
        ],
    },
    {
        "name": "b_and_h_serp",
        "vertical": "Ecommerce",
        "entity_type": "SERP",
        "data_source": "B&H",
        "is_localization_supported": False,
        "input_properties": [
            {"name": "search_query", "is_required": True},
        ],
    },
    {
        "name": "sams_club_plp",
        "vertical": "Ecommerce",
        "entity_type": "Search PLP",
        "data_source": "Sam's Club",
        "is_localization_supported": False,
        "input_properties": [
            {"name": "keyword", "is_required": True},
        ],
    },
    {
        "name": "some_social_agent",
        "vertical": "Social",
        "entity_type": "Profile",
        "data_source": "Twitter",
        "input_properties": [],
    },
]

MOCK_AMAZON_RESULTS = {
    "results": [
        {
            "product_name": "Logitech MX Keys",
            "price": "$99.99",
            "rating": "4.7",
            "review_count": "5,230",
            "product_url": "https://amazon.com/dp/B123",
            "image_url": "https://images.amazon.com/mx-keys.jpg",
            "brand": "Logitech",
        },
        {
            "product_name": "Keychron K2 Pro",
            "price": 79.99,
            "rating": 4.5,
            "review_count": 1200,
            "product_url": "https://amazon.com/dp/B456",
            "image_url": "https://images.amazon.com/k2pro.jpg",
        },
    ]
}

MOCK_BH_RESULTS = {
    "results": [
        {
            "name": "Apple Magic Keyboard",
            "price": "129.00",
            "stars": "4.3",
            "reviews_count": "890",
            "url": "https://bhphotovideo.com/apple-magic",
            "image": "https://images.bhphoto.com/magic.jpg",
            "brand_name": "Apple",
        },
    ]
}


def _make_adapter(api_key="test-key", mode="auto"):
    """Create a NimbleAdapter with a test API key."""
    with patch.dict("os.environ", {"NIMBLE_API_KEY": api_key} if api_key else {}, clear=False):
        return NimbleAdapter(api_key=api_key, mode=mode)


def _mock_response(json_data, status_code=200):
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


class TestNimbleAdapterNoKey:
    """Tests for seed/auto mode with no API key."""

    def test_no_key_returns_empty(self):
        adapter = NimbleAdapter(mode="seed")
        result = adapter.search("keyboard")
        assert result == []

    def test_auto_mode_no_key_returns_empty(self):
        with patch.dict("os.environ", {}, clear=False):
            # Remove NIMBLE_API_KEY if it happens to be set
            import os
            env = os.environ.copy()
            env.pop("NIMBLE_API_KEY", None)
            with patch.dict("os.environ", env, clear=True):
                adapter = NimbleAdapter(mode="auto")
                assert not adapter.use_api
                result = adapter.search("keyboard")
                assert result == []


class TestDiscoverTemplates:
    """Tests for dynamic template discovery."""

    def test_filters_ecommerce_serp_templates(self):
        adapter = _make_adapter()
        with patch.object(adapter, "_get", return_value=_mock_response(MOCK_AGENTS_RESPONSE)):
            templates = adapter._discover_templates()
        # Should include amazon_serp, b_and_h_serp, sams_club_plp (PLP matches)
        # Should exclude some_social_agent
        names = [t["name"] for t in templates]
        assert "amazon_serp" in names
        assert "b_and_h_serp" in names
        assert "sams_club_plp" in names
        assert "some_social_agent" not in names

    def test_caches_templates(self):
        adapter = _make_adapter()
        mock_get = MagicMock(return_value=_mock_response(MOCK_AGENTS_RESPONSE))
        with patch.object(adapter, "_get", mock_get):
            adapter._discover_templates()
            adapter._discover_templates()
        # Should only call the API once (cached)
        assert mock_get.call_count == 1


class TestInputFieldMapping:
    """Tests for input field name extraction from templates."""

    def test_keyword_field(self):
        adapter = _make_adapter()
        template = MOCK_AGENTS_RESPONSE[0]  # amazon_serp uses "keyword"
        assert adapter._get_input_field(template) == "keyword"

    def test_search_query_field(self):
        adapter = _make_adapter()
        template = MOCK_AGENTS_RESPONSE[1]  # b_and_h_serp uses "search_query"
        assert adapter._get_input_field(template) == "search_query"

    def test_fallback_to_first_property(self):
        adapter = _make_adapter()
        template = {
            "input_properties": [{"name": "custom_field", "is_required": False}]
        }
        assert adapter._get_input_field(template) == "custom_field"

    def test_fallback_to_keyword_default(self):
        adapter = _make_adapter()
        template = {"input_properties": []}
        assert adapter._get_input_field(template) == "keyword"


class TestParseResults:
    """Tests for result parsing into Product objects."""

    def test_parse_amazon_results(self):
        adapter = _make_adapter()
        products = adapter._parse_results(MOCK_AMAZON_RESULTS["results"], "Amazon")

        assert len(products) == 2

        p1 = products[0]
        assert isinstance(p1, Product)
        assert p1.source_site == "Amazon"
        assert p1.product_title == "Logitech MX Keys"
        assert p1.price_usd == 99.99
        assert p1.rating_avg == 4.7
        assert p1.rating_count == 5230
        assert p1.product_url == "https://amazon.com/dp/B123"
        assert p1.image_url == "https://images.amazon.com/mx-keys.jpg"
        assert p1.brand == "Logitech"

        p2 = products[1]
        assert p2.product_title == "Keychron K2 Pro"
        assert p2.price_usd == 79.99
        assert p2.rating_count == 1200
        # Brand extracted from title (first word) since no brand field
        assert p2.brand == "Keychron"

    def test_parse_bh_results_different_schema(self):
        adapter = _make_adapter()
        products = adapter._parse_results(MOCK_BH_RESULTS["results"], "B&H")

        assert len(products) == 1
        p = products[0]
        assert p.source_site == "B&H"
        assert p.product_title == "Apple Magic Keyboard"
        assert p.price_usd == 129.0
        assert p.rating_avg == 4.3
        assert p.rating_count == 890
        assert p.product_url == "https://bhphotovideo.com/apple-magic"
        assert p.brand == "Apple"

    def test_skips_items_without_title(self):
        adapter = _make_adapter()
        items = [{"price": "10.00"}, {"product_name": "Good Product", "price": "20.00"}]
        products = adapter._parse_results(items, "Test")
        assert len(products) == 1
        assert products[0].product_title == "Good Product"


class TestTemplateFailureIsolation:
    """Tests that one template failing doesn't break the others."""

    def test_failed_template_skipped(self):
        adapter = _make_adapter()

        # Two templates: first one will fail, second will succeed
        templates = [MOCK_AGENTS_RESPONSE[0], MOCK_AGENTS_RESPONSE[1]]
        adapter._templates = templates  # pre-cache

        call_count = 0

        def mock_run_template(template, query, zip_code):
            nonlocal call_count
            call_count += 1
            if template["name"] == "amazon_serp":
                raise httpx.HTTPStatusError(
                    "403 Forbidden",
                    request=MagicMock(),
                    response=MagicMock(status_code=403),
                )
            return MOCK_BH_RESULTS["results"]

        def mock_search_general(query):
            return []

        with patch.object(adapter, "_run_template", side_effect=mock_run_template):
            with patch.object(adapter, "_search_general", return_value=[]):
                products = adapter.search("keyboard")

        # Should have results from the second template only
        assert len(products) == 1
        assert products[0].source_site == "B&H"
        # Both templates were attempted
        assert call_count == 2

    def test_general_search_failure_isolated(self):
        adapter = _make_adapter()
        adapter._templates = []  # no templates

        with patch.object(adapter, "_search_general", side_effect=Exception("Network error")):
            products = adapter.search("keyboard")

        assert products == []


class TestLocalization:
    """Tests for zip_code / localization support."""

    def test_localization_supported_passes_zip(self):
        adapter = _make_adapter()
        template = MOCK_AGENTS_RESPONSE[0]  # amazon_serp, localization supported

        with patch.object(adapter, "_post", return_value=_mock_response({"results": []})) as mock_post:
            adapter._run_template(template, "keyboard", "90210")

        call_body = mock_post.call_args
        assert call_body[1]["json"]["params"]["zip_code"] == "90210"

    def test_localization_not_supported_no_zip(self):
        adapter = _make_adapter()
        template = MOCK_AGENTS_RESPONSE[1]  # b_and_h_serp, no localization

        with patch.object(adapter, "_post", return_value=_mock_response({"results": []})) as mock_post:
            adapter._run_template(template, "keyboard", "90210")

        call_body = mock_post.call_args
        assert "zip_code" not in call_body[1]["json"]["params"]


class TestSourceNameMapping:
    """Tests for template name -> display name mapping."""

    def test_known_templates_get_friendly_names(self):
        adapter = _make_adapter()
        adapter._templates = [MOCK_AGENTS_RESPONSE[0]]  # amazon_serp

        with patch.object(adapter, "_run_template", return_value=MOCK_AMAZON_RESULTS["results"]):
            with patch.object(adapter, "_search_general", return_value=[]):
                products = adapter.search("keyboard")

        assert all(p.source_site == "Amazon" for p in products)
