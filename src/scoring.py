"""Scoring engine for ranking products.

Default: composite score = ergonomics (40%) + reviews (20%) + value (20%) + build quality (20%).

When a ScoringProfile is provided, dimensions and weights are determined dynamically.
Each dimension is scored 0-100 and then weighted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.schema import Product


@dataclass
class ScoreBreakdown:
    """Score breakdown for a single product.

    Uses a ``dimensions`` dict for dynamic scoring while preserving backward-
    compatible properties for the four legacy keyboard dimensions.
    """

    total: float
    dimensions: dict[str, float] = field(default_factory=dict)
    reason: str = ""

    # Backward compat for existing code that reads s.ergonomics, s.reviews, etc.
    @property
    def ergonomics(self) -> float:
        return self.dimensions.get("ergonomics", 0.0)

    @property
    def reviews(self) -> float:
        return self.dimensions.get("reviews", 0.0)

    @property
    def value(self) -> float:
        return self.dimensions.get("value", 0.0)

    @property
    def build(self) -> float:
        return self.dimensions.get("build", 0.0)


# ── Weights (must sum to 1.0) ────────────────────────────────────────────────
W_ERGO = 0.40
W_REVIEW = 0.20
W_VALUE = 0.20
W_BUILD = 0.20


def _get_field_value(product: Product, field_name: str) -> str:
    """Resolve a field value from a Product.

    Supports:
    - Top-level fields: ``"switch_type"`` -> ``product.switch_type``
    - Bool-check fields: ``"__bool__hot_swappable"`` -> ``"true"``/``"false"``
    - Nested extra fields: ``"extra.nimble_raw.features"`` -> deep lookup in ``product.extra``
    """
    if field_name.startswith("__bool__"):
        attr = field_name[len("__bool__"):]
        val = getattr(product, attr, False)
        return "true" if val else "false"

    if field_name.startswith("extra."):
        parts = field_name.split(".")[1:]  # skip "extra"
        obj: Any = product.extra
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part, "")
            else:
                return ""
        if isinstance(obj, bool):
            return "true" if obj else "false"
        return str(obj) if obj else ""

    val = getattr(product, field_name, "")
    if isinstance(val, bool):
        return "true" if val else "false"
    return str(val) if val else ""


def _score_keyword_dimension(product: Product, dimension: Any) -> float:
    """Score a product on a keyword-based dimension.

    Iterates over the dimension's rules, checks keyword presence in the
    specified field, sums points, and clamps to 0-100.
    """
    score = 0
    for rule in dimension.rules:
        keyword = rule["keyword"].lower()
        field_name = rule["field"]
        points = rule["points"]

        # Special handling for bool-check rules like "hot_swappable:true"
        if ":" in keyword and field_name.startswith("__bool__"):
            field_val = _get_field_value(product, field_name).lower()
            expected = keyword.split(":")[1]
            if field_val == expected:
                score += points
        else:
            field_val = _get_field_value(product, field_name).lower()
            if keyword in field_val:
                score += points

    return max(0, min(score, 100))


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


def score_product(p: Product, profile: Any | None = None) -> ScoreBreakdown:
    """Compute composite score for a product.

    When *profile* is ``None``, uses the legacy hardcoded keyboard scoring.
    When a ``ScoringProfile`` is provided, evaluates each dimension dynamically.
    """
    if profile is None:
        # Legacy keyboard scoring (identical to original behavior)
        ergo = score_ergonomics(p)
        review = score_reviews(p)
        val = score_value(p)
        bld = score_build(p)

        total = ergo * W_ERGO + review * W_REVIEW + val * W_VALUE + bld * W_BUILD

        return ScoreBreakdown(
            total=round(total, 1),
            dimensions={
                "ergonomics": round(ergo, 1),
                "reviews": round(review, 1),
                "value": round(val, 1),
                "build": round(bld, 1),
            },
        )

    # Dynamic profile-based scoring
    dims: dict[str, float] = {}
    total = 0.0

    for dim in profile.dimensions:
        if dim.scoring_type == "keyword":
            dim_score = _score_keyword_dimension(p, dim)
        elif dim.scoring_type == "formula_reviews":
            dim_score = score_reviews(p)
        elif dim.scoring_type == "formula_value":
            dim_score = score_value(p)
        else:
            dim_score = 0.0

        dims[dim.name] = round(dim_score, 1)
        total += dim_score * dim.weight

    return ScoreBreakdown(total=round(total, 1), dimensions=dims)


def rank_products(
    products: list[Product],
    top_n: int = 10,
    deduplicate: bool = True,
    profile: Any | None = None,
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

    scored = [(p, score_product(p, profile=profile)) for p in products]
    scored.sort(key=lambda x: -x[1].total)
    return scored[:top_n]
