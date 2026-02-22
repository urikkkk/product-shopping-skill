"""Preference-based ranking boost.

Boosts products that match user-specified preferences (brand, feature, switch type, etc.).
"""

from __future__ import annotations

from src.schema import Product
from src.scoring import ScoreBreakdown

BOOST_PER_MATCH = 5
SCORE_CAP = 100


def apply_preferences(
    scored: list[tuple[Product, ScoreBreakdown]],
    preferences_str: str,
) -> list[tuple[Product, ScoreBreakdown]]:
    """Boost and re-sort products based on user preferences.

    Each keyword in the comma-separated preferences_str is matched against the
    product's brand, product_title, ergonomic_features, switch_type, switch_brand,
    programmable, connectivity, and category fields. Each match adds +5 to the
    total score (capped at 100). Products are re-sorted by total after boosting.

    Args:
        scored: List of (Product, ScoreBreakdown) tuples.
        preferences_str: Comma-separated preference keywords (e.g. "Keychron, split, QMK").

    Returns:
        Re-sorted list with boosted scores.
    """
    if not preferences_str or not preferences_str.strip():
        return scored

    keywords = [kw.strip().lower() for kw in preferences_str.split(",") if kw.strip()]
    if not keywords:
        return scored

    boosted: list[tuple[Product, ScoreBreakdown]] = []
    for product, breakdown in scored:
        searchable = " ".join([
            product.brand,
            product.product_title,
            product.ergonomic_features,
            product.switch_type,
            product.switch_brand,
            product.programmable,
            product.connectivity,
            product.category,
        ]).lower()

        match_count = sum(1 for kw in keywords if kw in searchable)
        new_total = min(breakdown.total + match_count * BOOST_PER_MATCH, SCORE_CAP)

        new_breakdown = ScoreBreakdown(
            total=round(new_total, 1),
            ergonomics=breakdown.ergonomics,
            reviews=breakdown.reviews,
            value=breakdown.value,
            build=breakdown.build,
            reason=breakdown.reason,
        )
        boosted.append((product, new_breakdown))

    boosted.sort(key=lambda x: -x[1].total)
    return boosted
