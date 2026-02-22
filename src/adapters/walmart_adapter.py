"""Walmart adapter.

Supports two modes:
1. **API mode**: Uses Walmart Affiliate API if WALMART_API_KEY is set.
2. **Seed mode** (default): Returns a small curated dataset.
"""

from __future__ import annotations

import logging

from src.schema import Product

from .base import BaseAdapter

logger = logging.getLogger(__name__)


_SEED_PRODUCTS: list[dict] = [
    {"product_title": "Kinesis Advantage360 Professional", "brand": "Kinesis", "price_usd": 529, "rating_avg": 4.4, "rating_count": 89, "layout_size": "Split Contoured", "switch_type": "Cherry MX Brown", "switch_brand": "Cherry", "connectivity": "Bluetooth + USB-C", "hot_swappable": True, "programmable": "ZMK (Open Source)", "ergonomic_features": "Split, Tented, Contoured keywells, Thumb clusters", "product_url": "https://www.walmart.com/ip/5607615601", "category": "Premium Split"},
    {"product_title": "Logitech Ergo K860", "brand": "Logitech", "price_usd": 119, "rating_avg": 4.5, "rating_count": 3200, "layout_size": "Wave Split Full", "switch_type": "Membrane (not mechanical)", "switch_brand": "Logitech", "connectivity": "Bluetooth + USB Receiver", "hot_swappable": False, "programmable": "Logi Options+", "ergonomic_features": "Split wave, Tented, Padded wrist rest, Negative tilt", "product_url": "https://www.walmart.com/ip/logitech-k860", "category": "Wave/Ergo"},
    {"product_title": "Microsoft Sculpt Ergonomic Keyboard", "brand": "Microsoft", "price_usd": 39, "rating_avg": 4.3, "rating_count": 5800, "layout_size": "Split Dome Full", "switch_type": "Membrane", "switch_brand": "Microsoft", "connectivity": "USB Receiver", "hot_swappable": False, "programmable": "No", "ergonomic_features": "Split dome, Tented, Padded wrist rest, Separate numpad", "product_url": "https://www.walmart.com/ip/microsoft-sculpt", "category": "Budget Ergo"},
    {"product_title": "Redragon K596 Vishnu TKL", "brand": "Redragon", "price_usd": 59, "rating_avg": 4.3, "rating_count": 410, "layout_size": "Standard TKL", "switch_type": "Redragon Brown", "switch_brand": "Redragon", "connectivity": "Bluetooth + USB-C", "hot_swappable": True, "programmable": "Software", "ergonomic_features": "Standard TKL, Wireless", "product_url": "https://www.walmart.com/ip/redragon-k596", "category": "Standard"},
]


class WalmartAdapter(BaseAdapter):
    """Walmart product adapter."""

    name = "walmart"
    _min_delay = 1.0

    def search(
        self,
        query: str,
        zip_code: str = "11201",
        max_results: int = 100,
    ) -> list[Product]:
        if self.use_api:
            return self._search_api(query, zip_code, max_results)
        return self._search_seed(query, zip_code, max_results)

    def _search_api(self, query: str, zip_code: str, max_results: int) -> list[Product]:
        """Search using Walmart Affiliate API."""
        logger.info("[Walmart] API mode — querying search API")
        products = []
        try:
            resp = self._get(
                "https://developer.api.walmart.com/api-proxy/service/affil/product/v2/search",
                params={"query": query, "numItems": str(min(max_results, 25))},
                headers={"WM_SEC.ACCESS_TOKEN": self.api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                products.append(
                    Product(
                        source_site="Walmart",
                        product_title=item.get("name", ""),
                        brand=item.get("brandName", ""),
                        price_usd=float(item.get("salePrice", 0)),
                        rating_avg=float(item.get("customerRating", 0)),
                        rating_count=int(item.get("numReviews", 0)),
                        availability="In Stock" if item.get("availableOnline") else "Out of Stock",
                        ship_to_zip=zip_code,
                        product_url=item.get("productUrl", ""),
                        image_url=item.get("thumbnailImage", ""),
                        ergonomic_features=item.get("shortDescription", ""),
                        category="Walmart",
                    )
                )
        except Exception:
            logger.exception("[Walmart] API request failed, falling back to seed data")
            return self._search_seed(query, zip_code, max_results)
        return products

    def _search_seed(self, query: str, zip_code: str, max_results: int) -> list[Product]:
        """Return curated seed data."""
        logger.info("[Walmart] Seed mode — returning %d products", len(_SEED_PRODUCTS))
        return [
            Product(
                source_site="Walmart",
                product_title=d["product_title"],
                brand=d["brand"],
                price_usd=d["price_usd"],
                rating_avg=d["rating_avg"],
                rating_count=d["rating_count"],
                availability="In Stock",
                ship_to_zip=zip_code,
                product_url=d["product_url"],
                layout_size=d["layout_size"],
                switch_type=d["switch_type"],
                switch_brand=d.get("switch_brand", ""),
                hot_swappable=d["hot_swappable"],
                connectivity=d["connectivity"],
                programmable=d.get("programmable", ""),
                ergonomic_features=d["ergonomic_features"],
                category=d["category"],
            )
            for d in _SEED_PRODUCTS[:max_results]
        ]
