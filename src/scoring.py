"""Scoring engine for ranking keyboards.

Composite score = ergonomics (40%) + reviews (20%) + value (20%) + build quality (20%).

Each dimension is scored 0-100 and then weighted.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.schema import Product


@dataclass
class ScoreBreakdown:
    """Score breakdown for a single product."""

    total: float
    ergonomics: float
    reviews: float
    value: float
    build: float
    reason: str = ""


# ── Weights (must sum to 1.0) ────────────────────────────────────────────────
W_ERGO = 0.40
W_REVIEW = 0.20
W_VALUE = 0.20
W_BUILD = 0.20


def score_ergonomics(p: Product) -> float:
    """Score ergonomic features 0-100."""
    features = p.ergonomic_features.lower()
    score = 0
    if "split" in features:
        score += 30
    if "tent" in features:
        score += 20
    if "tilt" in features or "negative tilt" in features:
        score += 10
    if "wrist rest" in features or "palm" in features:
        score += 10
    if "contour" in features:
        score += 15
    if "thumb" in features:
        score += 10
    if "ortholinear" in features or "columnar" in features:
        score += 5
    return min(score, 100)


def score_reviews(p: Product) -> float:
    """Score based on rating quality and quantity 0-100."""
    rating_part = (p.rating_avg / 5.0) * 70
    count_part = min(p.rating_count / 100, 30)
    return rating_part + count_part


def score_value(p: Product) -> float:
    """Score value for money 0-100. Lower price = higher score."""
    return max(0, 100 - (p.price_usd / 5))


def score_build(p: Product) -> float:
    """Score build quality and features 0-100."""
    score = 0
    switch = p.switch_type.lower()

    # Penalize non-mechanical
    if "membrane" in switch:
        score -= 30

    if p.hot_swappable:
        score += 25

    prog = p.programmable.lower()
    if any(kw in prog for kw in ("qmk", "via", "zmk")):
        score += 30

    conn = p.connectivity.lower()
    if "bluetooth" in conn or "2.4" in conn:
        score += 15

    brand = p.switch_brand.lower()
    if brand in ("cherry", "kailh", "gateron"):
        score += 15

    if "aluminum" in p.ergonomic_features.lower():
        score += 15

    return max(0, min(score, 100))


def score_product(p: Product) -> ScoreBreakdown:
    """Compute composite score for a product."""
    ergo = score_ergonomics(p)
    review = score_reviews(p)
    value = score_value(p)
    build = score_build(p)

    total = ergo * W_ERGO + review * W_REVIEW + value * W_VALUE + build * W_BUILD

    return ScoreBreakdown(
        total=round(total, 1),
        ergonomics=round(ergo, 1),
        reviews=round(review, 1),
        value=round(value, 1),
        build=round(build, 1),
    )


def rank_products(
    products: list[Product],
    top_n: int = 10,
    deduplicate: bool = True,
) -> list[tuple[Product, ScoreBreakdown]]:
    """Score and rank products, returning top N.

    When deduplicate=True, keeps the lowest-priced listing per brand+title.
    """
    if deduplicate:
        seen: dict[str, Product] = {}
        for p in products:
            key = f"{p.brand}|{p.product_title}"
            if key not in seen or p.price_usd < seen[key].price_usd:
                seen[key] = p
        products = list(seen.values())

    scored = [(p, score_product(p)) for p in products]
    scored.sort(key=lambda x: -x[1].total)
    return scored[:top_n]
