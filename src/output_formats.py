"""Stdout-friendly output formatters (text and JSON).

These complement the file-based writers in src/output.py by producing
output suitable for piping to other tools or AI agents.
"""

from __future__ import annotations

import json
from typing import Any

from src.enrichment.reviews import ProReview
from src.schema import Product
from src.scoring import ScoreBreakdown, W_BUILD, W_ERGO, W_REVIEW, W_VALUE


def _get_profile_dimensions(profile: Any | None) -> list[tuple[str, str, float]]:
    """Return list of (name, display_name, weight) from a profile, or keyboard defaults."""
    if profile is not None:
        return [(d.name, d.display_name, d.weight) for d in profile.dimensions]
    return [
        ("ergonomics", "Ergo", W_ERGO),
        ("reviews", "Review", W_REVIEW),
        ("value", "Value", W_VALUE),
        ("build", "Build", W_BUILD),
    ]


def format_text(
    ranked: list[tuple[Product, ScoreBreakdown]],
    reviews: dict[str, list[ProReview]],
    metadata: dict[str, Any] | None = None,
    profile: Any | None = None,
) -> str:
    """Format ranked results as a markdown table with score breakdown.

    Args:
        ranked: List of (Product, ScoreBreakdown) tuples from rank_products().
        reviews: Dict mapping product title to list of ProReview.
        metadata: Optional dict with query, mode, budget, etc.
        profile: Optional ScoringProfile for dynamic dimension headers.

    Returns:
        Markdown-formatted string suitable for stdout.
    """
    meta = metadata or {}
    lines: list[str] = []
    dims = _get_profile_dimensions(profile)

    # Header line
    parts = []
    if meta.get("query"):
        parts.append(f"Query: {meta['query']}")
    if meta.get("budget"):
        parts.append(f"Budget: ${meta['budget']:.0f}")
    if meta.get("mode"):
        parts.append(f"Mode: {meta['mode']}")
    parts.append(f"Results: {len(ranked)}")
    lines.append(f"**Product Shopping Results** | {' | '.join(parts)}")
    lines.append("")

    # Table header — dynamic dimension columns
    dim_headers = " | ".join(d[1] for d in dims)
    lines.append(
        f"| # | Product | Brand | Price | Score | {dim_headers} | Store |"
    )
    sep_parts = " | ".join("---" for _ in dims)
    lines.append(
        f"|---|---------|-------|-------|-------|{sep_parts}|-------|"
    )

    # Table rows
    for i, (p, s) in enumerate(ranked, 1):
        dim_vals = " | ".join(str(s.dimensions.get(d[0], 0.0)) for d in dims)
        lines.append(
            f"| {i} "
            f"| {p.product_title} "
            f"| {p.brand} "
            f"| ${p.price_usd:.0f} "
            f"| {s.total} "
            f"| {dim_vals} "
            f"| {p.source_site} |"
        )

    lines.append("")

    # Pro reviews section
    has_reviews = any(reviews.get(p.product_title) for p, _ in ranked)
    if has_reviews:
        lines.append("### Pro Reviews")
        lines.append("")
        for p, _ in ranked:
            revs = reviews.get(p.product_title, [])
            if revs:
                lines.append(f"**{p.product_title}**")
                for r in revs:
                    lines.append(f"- _{r.source}_: {r.verdict}")
                lines.append("")

    # Footer — dynamic weights
    weight_parts = ", ".join(f"{d[1]} {d[2]:.0%}" for d in dims)
    lines.append(f"_Scoring weights: {weight_parts}_")

    return "\n".join(lines)


def format_json(
    ranked: list[tuple[Product, ScoreBreakdown]],
    reviews: dict[str, list[ProReview]],
    metadata: dict[str, Any] | None = None,
    profile: Any | None = None,
) -> str:
    """Format ranked results as structured JSON.

    Args:
        ranked: List of (Product, ScoreBreakdown) tuples from rank_products().
        reviews: Dict mapping product title to list of ProReview.
        metadata: Optional dict with query, mode, budget, timing, etc.
        profile: Optional ScoringProfile for dynamic dimension weights.

    Returns:
        JSON string with metadata and results keys.
    """
    meta = metadata or {}
    dims = _get_profile_dimensions(profile)
    meta["scoring_weights"] = {d[0]: d[2] for d in dims}
    meta["result_count"] = len(ranked)

    results: list[dict[str, Any]] = []
    for rank, (p, s) in enumerate(ranked, 1):
        revs = reviews.get(p.product_title, [])
        result: dict[str, Any] = {
            "rank": rank,
            "product_title": p.product_title,
            "brand": p.brand,
            "price_usd": p.price_usd,
            "rating_avg": p.rating_avg,
            "rating_count": p.rating_count,
            "source_site": p.source_site,
            "product_url": p.product_url,
            "layout_size": p.layout_size,
            "switch_type": p.switch_type,
            "connectivity": p.connectivity,
            "hot_swappable": p.hot_swappable,
            "programmable": p.programmable,
            "ergonomic_features": p.ergonomic_features,
            "category": p.category,
            "scores": {"total": s.total, **s.dimensions},
            "pro_reviews": [
                {
                    "source": r.source,
                    "verdict": r.verdict,
                    "pros": r.pros,
                    "cons": r.cons,
                    "best_for": r.best_for,
                    "ergo_notes": r.ergo_notes,
                }
                for r in revs
            ],
        }
        results.append(result)

    output = {"metadata": meta, "results": results}
    return json.dumps(output, indent=2)
