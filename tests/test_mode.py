"""Tests for the mode flag in adapters."""

import os
from unittest.mock import patch

import pytest

from src.adapters.amazon_adapter import AmazonAdapter
from src.adapters.base import MissingAPIKeyError
from src.adapters.bestbuy_adapter import BestBuyAdapter
from src.adapters.walmart_adapter import WalmartAdapter


class TestModeFlag:
    def test_seed_mode_ignores_keys(self):
        """Seed mode should work without any API keys."""
        with patch.dict(os.environ, {}, clear=True):
            adapter = AmazonAdapter(mode="seed")
            assert adapter.use_api is False
            products = adapter.search("keyboard")
            assert len(products) > 0

    def test_seed_mode_bestbuy(self):
        adapter = BestBuyAdapter(mode="seed")
        assert adapter.use_api is False
        products = adapter.search("keyboard")
        assert len(products) > 0

    def test_seed_mode_walmart(self):
        adapter = WalmartAdapter(mode="seed")
        assert adapter.use_api is False
        products = adapter.search("keyboard")
        assert len(products) > 0

    def test_online_mode_without_key_raises(self):
        """Online mode without API key should raise MissingAPIKeyError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingAPIKeyError) as exc_info:
                BestBuyAdapter(mode="online")
            assert "BESTBUY_API_KEY" in str(exc_info.value)

    def test_online_amazon_without_keys_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingAPIKeyError) as exc_info:
                AmazonAdapter(mode="online")
            assert "AMAZON_ACCESS_KEY" in str(exc_info.value)

    def test_online_walmart_without_key_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(MissingAPIKeyError) as exc_info:
                WalmartAdapter(mode="online")
            assert "WALMART_API_KEY" in str(exc_info.value)

    def test_auto_mode_falls_back_to_seed(self):
        """Auto mode without keys should fall back to seed data."""
        with patch.dict(os.environ, {}, clear=True):
            adapter = BestBuyAdapter(mode="auto")
            assert adapter.use_api is False
            products = adapter.search("keyboard")
            assert len(products) > 0

    def test_auto_mode_uses_api_when_key_present(self):
        """Auto mode with API key should set use_api=True."""
        adapter = BestBuyAdapter(api_key="fake-key-for-test", mode="auto")
        assert adapter.use_api is True

    def test_default_mode_is_auto(self):
        adapter = BestBuyAdapter()
        assert adapter.mode == "auto"


class TestMissingAPIKeyError:
    def test_error_message_contains_env_vars(self):
        err = MissingAPIKeyError("bestbuy", ["BESTBUY_API_KEY"])
        assert "BESTBUY_API_KEY" in str(err)
        assert "bestbuy" in str(err)

    def test_error_message_with_setup_url(self):
        err = MissingAPIKeyError("bestbuy", ["BESTBUY_API_KEY"], "https://example.com/setup")
        assert "https://example.com/setup" in str(err)

    def test_error_attributes(self):
        err = MissingAPIKeyError("test", ["KEY1", "KEY2"], "https://example.com")
        assert err.adapter_name == "test"
        assert err.env_vars == ["KEY1", "KEY2"]
        assert err.setup_url == "https://example.com"
