"""Product filtering utilities.

Extracted from run_pipeline.py for reuse across entry points.
"""

from __future__ import annotations

from src.schema import Product


def apply_filters(
    products: list[Product],
    budget: float | None = None,
    wireless: str | None = None,
    layout: str | None = None,
    min_rating_count: int = 0,
) -> list[Product]:
    """Apply user-specified filters to a product list.

    Args:
        products: List of products to filter.
        budget: Maximum price in USD (None = no limit).
        wireless: "yes" to require wireless, "no" to exclude wireless, None to skip.
        layout: Layout keyword to match (e.g. "split", "alice", "ortho"). None to skip.
        min_rating_count: Minimum number of reviews required.

    Returns:
        Filtered list of products.
    """
    filtered = products

    if budget is not None:
        filtered = [p for p in filtered if p.price_usd <= budget]

    if wireless == "yes":
        filtered = [
            p for p in filtered
            if any(kw in p.connectivity.lower() for kw in ("bluetooth", "2.4"))
        ]
    elif wireless == "no":
        filtered = [
            p for p in filtered
            if not any(kw in p.connectivity.lower() for kw in ("bluetooth", "2.4"))
        ]

    if layout:
        layout_kw = layout.lower()
        filtered = [
            p for p in filtered
            if layout_kw in p.layout_size.lower() or layout_kw in p.category.lower()
        ]

    if min_rating_count:
        filtered = [p for p in filtered if p.rating_count >= min_rating_count]

    return filtered
