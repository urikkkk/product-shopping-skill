"""CSV / BYO adapter.

Lets users bring their own data as a CSV file. This is the recommended way to
add data from retailers that don't have a public API.
"""

from __future__ import annotations

import csv
import logging

from src.schema import Product, normalize_bool, normalize_price, normalize_rating

logger = logging.getLogger(__name__)


class CSVAdapter:
    """Load products from a user-provided CSV file."""

    name = "csv"

    def __init__(self, file_path: str = "", **kwargs):
        self.file_path = file_path

    def search(
        self,
        query: str = "",
        zip_code: str = "11201",
        max_results: int = 10000,
    ) -> list[Product]:
        if not self.file_path:
            logger.warning("[CSV] No file_path provided — returning empty list")
            return []

        logger.info("[CSV] Loading products from %s", self.file_path)
        products = []
        with open(self.file_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append(
                    Product(
                        source_site=row.get("source_site", row.get("store", "CSV")),
                        product_title=row.get("product_title", row.get("title", "")),
                        brand=row.get("brand", ""),
                        model=row.get("model", ""),
                        price_usd=normalize_price(row.get("price_usd", row.get("price", 0))),
                        availability=row.get("availability", ""),
                        ship_to_zip=row.get("ship_to_zip", zip_code),
                        product_url=row.get("product_url", ""),
                        image_url=row.get("image_url", ""),
                        layout_size=row.get("layout_size", row.get("layout", "")),
                        switch_type=row.get("switch_type", ""),
                        switch_brand=row.get("switch_brand", ""),
                        hot_swappable=normalize_bool(row.get("hot_swappable", False)),
                        connectivity=row.get("connectivity", ""),
                        programmable=row.get("programmable", ""),
                        ergonomic_features=row.get("ergonomic_features", ""),
                        rating_avg=normalize_rating(row.get("rating_avg", row.get("rating", 0))),
                        rating_count=int(float(row.get("rating_count", 0) or 0)),
                        category=row.get("category", ""),
                    )
                )
                if len(products) >= max_results:
                    break
        logger.info("[CSV] Loaded %d products", len(products))
        return products
