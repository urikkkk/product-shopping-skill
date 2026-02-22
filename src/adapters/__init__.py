"""Retailer adapters registry.

Each adapter implements the same interface:
    search(query: str, zip_code: str, max_results: int) -> list[Product]
"""

from __future__ import annotations

from typing import Protocol

from src.schema import Product

from .amazon_adapter import AmazonAdapter
from .bestbuy_adapter import BestBuyAdapter
from .csv_adapter import CSVAdapter
from .walmart_adapter import WalmartAdapter


class AdapterProtocol(Protocol):
    """Interface that every retailer adapter must satisfy."""

    name: str

    def search(
        self,
        query: str,
        zip_code: str = "11201",
        max_results: int = 100,
    ) -> list[Product]: ...


# Registry of built-in adapters (name -> class)
ADAPTER_REGISTRY: dict[str, type] = {
    "amazon": AmazonAdapter,
    "bestbuy": BestBuyAdapter,
    "walmart": WalmartAdapter,
    "csv": CSVAdapter,
}


def get_adapter(name: str, **kwargs) -> AdapterProtocol:
    """Instantiate an adapter by registry name."""
    cls = ADAPTER_REGISTRY.get(name.lower())
    if cls is None:
        available = ", ".join(sorted(ADAPTER_REGISTRY.keys()))
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return cls(**kwargs)


def list_adapters() -> list[str]:
    """Return list of registered adapter names."""
    return sorted(ADAPTER_REGISTRY.keys())
