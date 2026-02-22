"""Preference-based ranking boost.

Boosts products that match user-specified preferences (brand, feature, switch type, etc.).
"""

from __future__ import annotations

from typing import Any

from src.schema import Product
from src.scoring import ScoreBreakdown, _get_field_value

BOOST_PER_MATCH = 5
SCORE_CAP = 100

_DEFAULT_PREFERENCE_FIELDS = [
    "brand", "product_title", "ergonomic_features", "switch_type",
    "switch_brand", "programmable", "connectivity", "category",
]


def apply_preferences(
    scored: list[tuple[Product, ScoreBreakdown]],
    preferences_str: str,
    preference_fields: list[str] | None = None,
) -> list[tuple[Product, ScoreBreakdown]]:
    """Boost and re-sort products based on user preferences.

    Each keyword in the comma-separated preferences_str is matched against the
    product's searchable fields. Each match adds +5 to the total score (capped
    at 100). Products are re-sorted by total after boosting.

    Args:
        scored: List of (Product, ScoreBreakdown) tuples.
        preferences_str: Comma-separated preference keywords (e.g. "Keychron, split, QMK").
        preference_fields: Optional list of field names to search. Supports
            ``"extra.*"`` paths via :func:`_get_field_value`. Falls back to
            the default 8 keyboard fields when not provided.

    Returns:
        Re-sorted list with boosted scores.
    """
    if not preferences_str or not preferences_str.strip():
        return scored

    keywords = [kw.strip().lower() for kw in preferences_str.split(",") if kw.strip()]
    if not keywords:
        return scored

    fields = preference_fields or _DEFAULT_PREFERENCE_FIELDS

    boosted: list[tuple[Product, ScoreBreakdown]] = []
    for product, breakdown in scored:
        searchable = " ".join(
            _get_field_value(product, f) for f in fields
        ).lower()

        match_count = sum(1 for kw in keywords if kw in searchable)
        new_total = min(breakdown.total + match_count * BOOST_PER_MATCH, SCORE_CAP)

        new_breakdown = ScoreBreakdown(
            total=round(new_total, 1),
            dimensions=dict(breakdown.dimensions),
            reason=breakdown.reason,
        )
        boosted.append((product, new_breakdown))

    boosted.sort(key=lambda x: -x[1].total)
    return boosted
