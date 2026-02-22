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


def format_text(
    ranked: list[tuple[Product, ScoreBreakdown]],
    reviews: dict[str, list[ProReview]],
    metadata: dict[str, Any] | None = None,
) -> str:
    """Format ranked results as a markdown table with score breakdown.

    Args:
        ranked: List of (Product, ScoreBreakdown) tuples from rank_products().
        reviews: Dict mapping product title to list of ProReview.
        metadata: Optional dict with query, mode, budget, etc.

    Returns:
        Markdown-formatted string suitable for stdout.
    """
    meta = metadata or {}
    lines: list[str] = []

    # Header line
    parts = []
    if meta.get("query"):
        parts.append(f"Query: {meta['query']}")
    if meta.get("budget"):
        parts.append(f"Budget: ${meta['budget']:.0f}")
    if meta.get("mode"):
        parts.append(f"Mode: {meta['mode']}")
    parts.append(f"Results: {len(ranked)}")
    lines.append(f"**Keyboard Shopping Results** | {' | '.join(parts)}")
    lines.append("")

    # Table header
    lines.append(
        "| # | Product | Brand | Price | Score | Ergo | Review | Value | Build | Store |"
    )
    lines.append(
        "|---|---------|-------|-------|-------|------|--------|-------|-------|-------|"
    )

    # Table rows
    for i, (p, s) in enumerate(ranked, 1):
        lines.append(
            f"| {i} "
            f"| {p.product_title} "
            f"| {p.brand} "
            f"| ${p.price_usd:.0f} "
            f"| {s.total} "
            f"| {s.ergonomics} "
            f"| {s.reviews} "
            f"| {s.value} "
            f"| {s.build} "
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

    # Footer
    lines.append(
        f"_Scoring weights: Ergonomics {W_ERGO:.0%}, Reviews {W_REVIEW:.0%}, "
        f"Value {W_VALUE:.0%}, Build {W_BUILD:.0%}_"
    )

    return "\n".join(lines)


def format_json(
    ranked: list[tuple[Product, ScoreBreakdown]],
    reviews: dict[str, list[ProReview]],
    metadata: dict[str, Any] | None = None,
) -> str:
    """Format ranked results as structured JSON.

    Args:
        ranked: List of (Product, ScoreBreakdown) tuples from rank_products().
        reviews: Dict mapping product title to list of ProReview.
        metadata: Optional dict with query, mode, budget, timing, etc.

    Returns:
        JSON string with metadata and results keys.
    """
    meta = metadata or {}
    meta["scoring_weights"] = {
        "ergonomics": W_ERGO,
        "reviews": W_REVIEW,
        "value": W_VALUE,
        "build": W_BUILD,
    }
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
            "scores": {
                "total": s.total,
                "ergonomics": s.ergonomics,
                "reviews": s.reviews,
                "value": s.value,
                "build": s.build,
            },
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
