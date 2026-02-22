# How to Add a New Retailer Adapter

The pipeline is designed to be extended with new data sources. Here's how to
add support for a new retailer.

## Step 1: Create the adapter file

Create `src/adapters/yourstore_adapter.py`:

```python
"""Your Store adapter."""

from __future__ import annotations

import logging
from src.schema import Product
from .base import BaseAdapter

logger = logging.getLogger(__name__)


class YourStoreAdapter(BaseAdapter):
    """Your Store product adapter."""

    name = "yourstore"
    _min_delay = 1.0  # seconds between requests

    def search(
        self,
        query: str,
        zip_code: str = "11201",
        max_results: int = 100,
    ) -> list[Product]:
        if self.use_api:
            return self._search_api(query, zip_code, max_results)
        return self._search_seed(query, zip_code, max_results)

    def _search_api(self, query, zip_code, max_results):
        """Implement API-based search here."""
        logger.info("[YourStore] Searching via API...")
        # Use self._get(url, params=...) for throttled HTTP requests
        # Parse response and return list of Product objects
        return []

    def _search_seed(self, query, zip_code, max_results):
        """Return hardcoded seed data for testing."""
        return [
            Product(
                source_site="Your Store",
                product_title="Example Keyboard",
                brand="ExampleBrand",
                price_usd=149.99,
                rating_avg=4.3,
                rating_count=250,
                availability="In Stock",
                ship_to_zip=zip_code,
                layout_size="Standard TKL",
                switch_type="Cherry MX Brown",
                connectivity="USB-C",
                hot_swappable=True,
                ergonomic_features="Standard layout",
                category="Standard",
            )
        ]
```

## Step 2: Register it

In `src/adapters/__init__.py`, add:

```python
from .yourstore_adapter import YourStoreAdapter

ADAPTER_REGISTRY: dict[str, type] = {
    # ... existing adapters ...
    "yourstore": YourStoreAdapter,
}
```

## Step 3: Use it

```bash
python -m scripts.run_pipeline --adapters amazon bestbuy walmart yourstore
```

## Step 4: Add tests

Create `tests/test_yourstore_adapter.py`:

```python
from src.adapters.yourstore_adapter import YourStoreAdapter
from src.schema import Product

def test_seed_mode():
    adapter = YourStoreAdapter()
    products = adapter.search("keyboard")
    assert len(products) > 0
    assert all(isinstance(p, Product) for p in products)
```

## Alternative: BYO CSV

If you don't want to write code, you can export data from any source as a CSV
matching the schema (see `data/schema.json`) and use the CSV adapter:

```bash
python -m scripts.run_pipeline --csv-file my_data.csv
```

## Guidelines

- Always use `self._get()` instead of raw `httpx.get()` — it handles throttling
- Normalize data into `Product` objects before returning
- Prefer official APIs over scraping
- Respect rate limits and robots.txt
- Add seed data for offline/testing use
