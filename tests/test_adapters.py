"""Tests for retailer adapters."""

import os
import tempfile

from src.adapters import get_adapter, list_adapters
from src.adapters.amazon_adapter import AmazonAdapter
from src.adapters.bestbuy_adapter import BestBuyAdapter
from src.adapters.csv_adapter import CSVAdapter
from src.adapters.walmart_adapter import WalmartAdapter
from src.schema import Product


class TestAdapterRegistry:
    def test_list_adapters(self):
        adapters = list_adapters()
        assert "amazon" in adapters
        assert "bestbuy" in adapters
        assert "walmart" in adapters
        assert "csv" in adapters

    def test_get_adapter(self):
        adapter = get_adapter("amazon")
        assert isinstance(adapter, AmazonAdapter)

    def test_unknown_adapter_raises(self):
        try:
            get_adapter("nonexistent")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "nonexistent" in str(e)


class TestAmazonAdapter:
    def test_seed_mode_returns_products(self):
        adapter = AmazonAdapter()
        assert not adapter.use_api
        products = adapter.search("ergonomic keyboard")
        assert len(products) > 0
        assert all(isinstance(p, Product) for p in products)
        assert all(p.source_site == "Amazon" for p in products)

    def test_products_have_required_fields(self):
        adapter = AmazonAdapter()
        products = adapter.search("keyboard")
        for p in products:
            assert p.product_title
            assert p.brand
            assert p.price_usd > 0


class TestBestBuyAdapter:
    def test_seed_mode_returns_products(self):
        adapter = BestBuyAdapter()
        products = adapter.search("ergonomic keyboard")
        assert len(products) > 0
        assert all(p.source_site == "Best Buy" for p in products)


class TestWalmartAdapter:
    def test_seed_mode_returns_products(self):
        adapter = WalmartAdapter()
        products = adapter.search("ergonomic keyboard")
        assert len(products) > 0
        assert all(p.source_site == "Walmart" for p in products)


class TestCSVAdapter:
    def test_load_csv(self):
        csv_content = (
            "source_site,product_title,brand,price_usd,rating_avg,rating_count,"
            "layout_size,switch_type,connectivity,hot_swappable,ergonomic_features\n"
            "TestStore,Test KB,TestBrand,99.99,4.5,100,"
            "Split,Cherry MX,USB-C,True,Split Tented\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            f.flush()
            path = f.name

        try:
            adapter = CSVAdapter(file_path=path)
            products = adapter.search()
            assert len(products) == 1
            p = products[0]
            assert p.product_title == "Test KB"
            assert p.price_usd == 99.99
            assert p.hot_swappable is True
        finally:
            os.unlink(path)

    def test_no_file_returns_empty(self):
        adapter = CSVAdapter()
        assert adapter.search() == []
