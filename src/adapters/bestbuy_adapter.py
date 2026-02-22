"""Best Buy adapter.

Supports two modes:
1. **API mode**: Uses Best Buy Products API v1 if BESTBUY_API_KEY is set.
   Free key at https://developer.bestbuy.com/
2. **Seed mode** (default): Returns a small curated dataset.
"""

from __future__ import annotations

import logging

from src.schema import Product

from .base import BaseAdapter

logger = logging.getLogger(__name__)


_SEED_PRODUCTS: list[dict] = [
    {"product_title": "Logitech Ergo K860", "brand": "Logitech", "price_usd": 129, "rating_avg": 4.4, "rating_count": 890, "layout_size": "Wave Split Full", "switch_type": "Membrane (not mechanical)", "switch_brand": "Logitech", "connectivity": "Bluetooth + USB Receiver", "hot_swappable": False, "programmable": "Logi Options+", "ergonomic_features": "Split wave, Tented, Padded wrist rest, Negative tilt", "product_url": "https://www.bestbuy.com/site/logitech-ergo-k860/6395346.p", "category": "Wave/Ergo"},
    {"product_title": "Logitech MX Keys S", "brand": "Logitech", "price_usd": 109, "rating_avg": 4.6, "rating_count": 2100, "layout_size": "Standard Full", "switch_type": "Low-Profile Membrane", "switch_brand": "Logitech", "connectivity": "Bluetooth + USB Receiver", "hot_swappable": False, "programmable": "Logi Options+", "ergonomic_features": "Low-profile, Backlit, Multi-device", "product_url": "https://www.bestbuy.com/site/logitech-mx-keys-s/6539505.p", "category": "Standard"},
    {"product_title": "Corsair K70 RGB Pro", "brand": "Corsair", "price_usd": 159, "rating_avg": 4.5, "rating_count": 650, "layout_size": "Standard Full", "switch_type": "Cherry MX Red", "switch_brand": "Cherry", "connectivity": "USB", "hot_swappable": False, "programmable": "iCUE", "ergonomic_features": "Wrist rest, Standard layout", "product_url": "https://www.bestbuy.com/site/corsair-k70-rgb-pro/6502560.p", "category": "Gaming"},
    {"product_title": "Microsoft Ergonomic Keyboard", "brand": "Microsoft", "price_usd": 59, "rating_avg": 4.2, "rating_count": 1500, "layout_size": "Split Wave Full", "switch_type": "Membrane", "switch_brand": "Microsoft", "connectivity": "USB", "hot_swappable": False, "programmable": "No", "ergonomic_features": "Split, Tented, Padded wrist rest", "product_url": "https://www.bestbuy.com/site/microsoft-ergonomic-keyboard/6378567.p", "category": "Budget Ergo"},
]


class BestBuyAdapter(BaseAdapter):
    """Best Buy product adapter."""

    name = "bestbuy"
    _min_delay = 0.5

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
        """Search using Best Buy Products API v1."""
        logger.info("[BestBuy] API mode — querying products API")
        products = []
        try:
            page_size = min(max_results, 100)
            resp = self._get(
                "https://api.bestbuy.com/v1/products",
                params={
                    "apiKey": self.api_key,
                    "format": "json",
                    f"(search={query})": "",
                    "show": "sku,name,manufacturer,salePrice,url,image,"
                    "customerReviewAverage,customerReviewCount,"
                    "shortDescription,onlineAvailability",
                    "pageSize": str(page_size),
                    "page": "1",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("products", []):
                products.append(
                    Product(
                        source_site="Best Buy",
                        product_title=item.get("name", ""),
                        brand=item.get("manufacturer", ""),
                        price_usd=float(item.get("salePrice", 0)),
                        rating_avg=float(item.get("customerReviewAverage", 0)),
                        rating_count=int(item.get("customerReviewCount", 0)),
                        availability="In Stock" if item.get("onlineAvailability") else "Out of Stock",
                        ship_to_zip=zip_code,
                        product_url=item.get("url", ""),
                        image_url=item.get("image", ""),
                        ergonomic_features=item.get("shortDescription", ""),
                        category="Best Buy",
                    )
                )
        except Exception:
            logger.exception("[BestBuy] API request failed, falling back to seed data")
            return self._search_seed(query, zip_code, max_results)
        return products

    def _search_seed(self, query: str, zip_code: str, max_results: int) -> list[Product]:
        """Return curated seed data."""
        logger.info("[BestBuy] Seed mode — returning %d products", len(_SEED_PRODUCTS))
        return [
            Product(
                source_site="Best Buy",
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
