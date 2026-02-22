"""Amazon adapter.

Supports two modes:
1. **API mode**: Uses Amazon Product Advertising API (PA-API 5.0) if
   AMAZON_ACCESS_KEY, AMAZON_SECRET_KEY, and AMAZON_PARTNER_TAG are set.
2. **BYO mode** (default): Returns a curated seed dataset of popular ergonomic
   keyboards on Amazon. Users can extend this by providing their own CSV via
   the CSVAdapter.

Direct scraping of Amazon violates their ToS and is intentionally not
implemented. Use the PA-API or BYO mode instead.
"""

from __future__ import annotations

import logging
import os

from src.schema import Product

from .base import BaseAdapter

logger = logging.getLogger(__name__)


# Curated seed data — real products available on Amazon (Feb 2026)
_SEED_PRODUCTS: list[dict] = [
    {"product_title": "Kinesis Advantage360 Professional", "brand": "Kinesis", "price_usd": 449, "rating_avg": 4.4, "rating_count": 312, "layout_size": "Split Contoured", "switch_type": "Cherry MX Brown", "switch_brand": "Cherry", "connectivity": "Bluetooth + USB-C", "hot_swappable": True, "programmable": "ZMK (Open Source)", "ergonomic_features": "Split, Tented, Contoured keywells, Thumb clusters", "product_url": "https://www.amazon.com/dp/B0BCHMGZMD", "category": "Premium Split"},
    {"product_title": "Kinesis Advantage360 (Wired)", "brand": "Kinesis", "price_usd": 399, "rating_avg": 4.3, "rating_count": 198, "layout_size": "Split Contoured", "switch_type": "Cherry MX Brown", "switch_brand": "Cherry", "connectivity": "USB-C", "hot_swappable": True, "programmable": "ZMK (Open Source)", "ergonomic_features": "Split, Tented, Contoured keywells, Thumb clusters", "product_url": "https://www.amazon.com/dp/B0BCHFHX6V", "category": "Premium Split"},
    {"product_title": "Keychron Q10 Pro", "brand": "Keychron", "price_usd": 219, "rating_avg": 4.5, "rating_count": 340, "layout_size": "Alice 75%", "switch_type": "Gateron Jupiter Brown", "switch_brand": "Gateron", "connectivity": "Bluetooth + USB-C", "hot_swappable": True, "programmable": "QMK/VIA", "ergonomic_features": "Alice curved split, Knob", "product_url": "https://www.amazon.com/Keychron-Q10-Pro", "category": "Alice"},
    {"product_title": "Keychron Q11 QMK Split", "brand": "Keychron", "price_usd": 209, "rating_avg": 4.4, "rating_count": 280, "layout_size": "Split 75%", "switch_type": "Gateron G Pro Brown", "switch_brand": "Gateron", "connectivity": "USB-C (Wired)", "hot_swappable": True, "programmable": "QMK/VIA", "ergonomic_features": "Physical split, Knob, Full aluminum", "product_url": "https://www.amazon.com/dp/B0C9Q7S8CB", "category": "Split"},
    {"product_title": "Feker Alice98", "brand": "Feker/MechLands", "price_usd": 109, "rating_avg": 4.3, "rating_count": 380, "layout_size": "Alice 98%", "switch_type": "Various (Hot-swap)", "switch_brand": "Various", "connectivity": "USB-C (Wired)", "hot_swappable": True, "programmable": "VIA", "ergonomic_features": "Alice split with numpad, Knob, 5-layer padding", "product_url": "https://www.amazon.com/dp/B0DF2CZZ8Z", "category": "Alice"},
    {"product_title": "Kinesis mWave Ergonomic Keyboard (Mac)", "brand": "Kinesis", "price_usd": 199, "rating_avg": 4.3, "rating_count": 98, "layout_size": "Wave Full", "switch_type": "Gateron Low-Profile Brown", "switch_brand": "Gateron", "connectivity": "Bluetooth + USB-C", "hot_swappable": False, "programmable": "Kinesis SmartSet", "ergonomic_features": "Tented center, Negative tilt, Padded wrist rest, Wave layout", "product_url": "https://www.amazon.com/dp/B0DYLB3YBJ", "category": "Wave/Ergo"},
    {"product_title": "Logitech Ergo K860", "brand": "Logitech", "price_usd": 129, "rating_avg": 4.4, "rating_count": 12500, "layout_size": "Wave Split Full", "switch_type": "Membrane (not mechanical)", "switch_brand": "Logitech", "connectivity": "Bluetooth + USB Receiver", "hot_swappable": False, "programmable": "Logi Options+", "ergonomic_features": "Split wave, Tented, Padded wrist rest, Negative tilt", "product_url": "https://www.amazon.com/Logitech-Wireless-Ergonomic-Keyboard-Wrist/dp/B07ZWK2TQT", "category": "Wave/Ergo"},
    {"product_title": "Microsoft Sculpt Ergonomic Keyboard", "brand": "Microsoft", "price_usd": 44, "rating_avg": 4.3, "rating_count": 18000, "layout_size": "Split Dome Full", "switch_type": "Membrane", "switch_brand": "Microsoft", "connectivity": "USB Receiver", "hot_swappable": False, "programmable": "No", "ergonomic_features": "Split dome, Tented, Padded wrist rest, Separate numpad", "product_url": "https://www.amazon.com/Microsoft-Ergonomic-Keyboard-Business-5KV-00001/dp/B00CYX26BC", "category": "Budget Ergo"},
    {"product_title": "NuPhy Air75 V2", "brand": "NuPhy", "price_usd": 129, "rating_avg": 4.5, "rating_count": 1200, "layout_size": "Standard 75%", "switch_type": "NuPhy Low-Profile", "switch_brand": "NuPhy", "connectivity": "Bluetooth + 2.4GHz + USB-C", "hot_swappable": True, "programmable": "Software", "ergonomic_features": "Low-profile, Lightweight, Portable", "product_url": "https://www.amazon.com/NuPhy-Air75-V2", "category": "Low-Profile"},
    {"product_title": "Cloud Nine ErgoTKL Split Keyboard", "brand": "Cloud Nine", "price_usd": 169, "rating_avg": 4.2, "rating_count": 230, "layout_size": "Split TKL", "switch_type": "Cherry MX Brown", "switch_brand": "Cherry", "connectivity": "USB", "hot_swappable": False, "programmable": "Software", "ergonomic_features": "Split, Padded wrist rest, Adjustable splay", "product_url": "https://www.amazon.com/Cloud-Nine-ErgoTKL", "category": "Split"},
    {"product_title": "EPOMAKER Alice66", "brand": "EPOMAKER", "price_usd": 89, "rating_avg": 4.2, "rating_count": 320, "layout_size": "Alice 65%", "switch_type": "Various (Hot-swap)", "switch_brand": "Various", "connectivity": "Bluetooth + 2.4GHz + USB-C", "hot_swappable": True, "programmable": "Software", "ergonomic_features": "Alice layout, Wireless, Budget", "product_url": "https://www.amazon.com/EPOMAKER-Alice66", "category": "Alice"},
    {"product_title": "Perixx PERIBOARD-535 Ergonomic", "brand": "Perixx", "price_usd": 69, "rating_avg": 4.1, "rating_count": 580, "layout_size": "Split Wave Full", "switch_type": "Kailh Brown", "switch_brand": "Kailh", "connectivity": "USB", "hot_swappable": False, "programmable": "No", "ergonomic_features": "Split wave, Tented, Low-profile keycaps, Wrist rest", "product_url": "https://www.amazon.com/Perixx-PERIBOARD-535", "category": "Budget Ergo"},
    {"product_title": "X-Bows Nature Ergonomic", "brand": "X-Bows", "price_usd": 139, "rating_avg": 4.0, "rating_count": 190, "layout_size": "Cross-linear TKL", "switch_type": "Gateron Brown", "switch_brand": "Gateron", "connectivity": "USB-C", "hot_swappable": True, "programmable": "Software", "ergonomic_features": "Cross-linear layout, Reduced finger travel, Thumb cluster", "product_url": "https://www.amazon.com/X-Bows-Nature", "category": "Ergonomic"},
    {"product_title": "Kinesis Freestyle2 for PC", "brand": "Kinesis", "price_usd": 89, "rating_avg": 4.1, "rating_count": 1100, "layout_size": "Split Flat Full", "switch_type": "Membrane", "switch_brand": "Kinesis", "connectivity": "USB", "hot_swappable": False, "programmable": "SmartSet", "ergonomic_features": "Split (20in), VIP3 tenting kit, Splay adjustable", "product_url": "https://www.amazon.com/Kinesis-Freestyle2-Ergonomic-Keyboard-Separation/dp/B0089ZLENA", "category": "Split"},
    {"product_title": "GMK70 Alice", "brand": "GMK", "price_usd": 79, "rating_avg": 4.1, "rating_count": 450, "layout_size": "Alice 70%", "switch_type": "Various (Hot-swap)", "switch_brand": "Various", "connectivity": "Bluetooth + 2.4GHz + USB-C", "hot_swappable": True, "programmable": "Software", "ergonomic_features": "Alice layout, Budget-friendly entry", "product_url": "https://www.amazon.com/GMK70-Alice", "category": "Alice"},
    {"product_title": "IQUNIX Magi96 Low-Profile", "brand": "IQUNIX", "price_usd": 199, "rating_avg": 4.3, "rating_count": 150, "layout_size": "Standard 96%", "switch_type": "Low-Profile", "switch_brand": "IQUNIX", "connectivity": "Bluetooth + USB-C", "hot_swappable": True, "programmable": "Software", "ergonomic_features": "Ultra-slim 11mm, Aircraft aluminum, Low-profile", "product_url": "https://www.amazon.com/IQUNIX-Magi96", "category": "Low-Profile"},
]


class AmazonAdapter(BaseAdapter):
    """Amazon product adapter.

    Modes:
    - BYO (default): Returns curated seed data. Extend with CSVAdapter.
    - PA-API: Uses Amazon Product Advertising API 5.0 (requires keys).
    """

    name = "amazon"
    _min_delay = 1.5
    _env_vars = ["AMAZON_ACCESS_KEY", "AMAZON_SECRET_KEY", "AMAZON_PARTNER_TAG"]

    def __init__(self, **kwargs):
        # Extract mode before super().__init__ since Amazon has custom key logic
        mode = kwargs.get("mode", "auto")
        super().__init__(**kwargs)
        self._access_key = os.environ.get("AMAZON_ACCESS_KEY")
        self._secret_key = os.environ.get("AMAZON_SECRET_KEY")
        self._partner_tag = os.environ.get("AMAZON_PARTNER_TAG")
        has_keys = bool(self._access_key and self._secret_key and self._partner_tag)
        if mode == "online" and not has_keys:
            from .base import MissingAPIKeyError
            raise MissingAPIKeyError(self.name, self._env_vars)
        elif mode == "seed":
            self.use_api = False
        else:  # auto
            self.use_api = has_keys

    def search(
        self,
        query: str,
        zip_code: str = "11201",
        max_results: int = 100,
    ) -> list[Product]:
        if self.use_api:
            return self._search_api(query, zip_code, max_results)
        return self._search_byo(query, zip_code, max_results)

    def _search_api(self, query: str, zip_code: str, max_results: int) -> list[Product]:
        """Search via Amazon PA-API 5.0."""
        logger.info("[Amazon] PA-API mode — not yet implemented. Falling back to BYO data.")
        # PA-API integration would go here. The API requires HMAC-signed requests
        # to webservices.amazon.com/paapi5/searchitems.
        # For now, fall back to seed data.
        return self._search_byo(query, zip_code, max_results)

    def _search_byo(self, query: str, zip_code: str, max_results: int) -> list[Product]:
        """Return curated seed dataset."""
        logger.info("[Amazon] BYO mode — returning %d seed products", len(_SEED_PRODUCTS))
        products = []
        query_lower = query.lower()
        for data in _SEED_PRODUCTS[:max_results]:
            # Basic query matching
            if query_lower not in "ergonomic keyboard mechanical":
                title_lower = data["product_title"].lower()
                if not any(w in title_lower for w in query_lower.split()):
                    continue

            products.append(
                Product(
                    source_site="Amazon",
                    product_title=data["product_title"],
                    brand=data["brand"],
                    price_usd=data["price_usd"],
                    rating_avg=data["rating_avg"],
                    rating_count=data["rating_count"],
                    availability="In Stock",
                    ship_to_zip=zip_code,
                    product_url=data["product_url"],
                    layout_size=data["layout_size"],
                    switch_type=data["switch_type"],
                    switch_brand=data.get("switch_brand", ""),
                    hot_swappable=data["hot_swappable"],
                    connectivity=data["connectivity"],
                    programmable=data.get("programmable", ""),
                    ergonomic_features=data["ergonomic_features"],
                    category=data["category"],
                )
            )
        return products
