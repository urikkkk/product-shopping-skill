"""Dynamic scoring profile generation.

Determines scoring dimensions, weights, and product-specific fields based on the
search query. Uses Claude (Sonnet) when ANTHROPIC_API_KEY is available, otherwise
falls back to the hardcoded keyboard profile that matches legacy scoring exactly.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ScoringDimension:
    """A single scoring dimension within a profile."""

    name: str  # "ergonomics", "comfort"
    weight: float  # 0.0-1.0
    display_name: str  # "Ergonomics", "Comfort"
    scoring_type: str  # "keyword" | "formula_reviews" | "formula_value"
    rules: list[dict] = field(default_factory=list)  # For keyword type
    description: str = ""


@dataclass
class ScoringProfile:
    """Describes how to score products for a given category."""

    category: str  # "ergonomic keyboards"
    dimensions: list[ScoringDimension] = field(default_factory=list)
    category_fields: list[str] = field(default_factory=list)  # Important fields
    preference_fields: list[str] = field(default_factory=list)  # For preference matching


def get_keyboard_profile() -> ScoringProfile:
    """Return the hardcoded keyboard profile matching legacy scoring exactly.

    This reproduces the same dimensions, weights, keywords, and points as the
    original ``score_ergonomics``, ``score_build``, ``score_reviews``, and
    ``score_value`` functions in ``src/scoring.py``.
    """
    return ScoringProfile(
        category="ergonomic keyboards",
        dimensions=[
            ScoringDimension(
                name="ergonomics",
                weight=0.40,
                display_name="Ergonomics",
                scoring_type="keyword",
                description="Ergonomic feature scoring based on split, tenting, tilt, etc.",
                rules=[
                    {"keyword": "split", "points": 30, "field": "ergonomic_features"},
                    {"keyword": "tent", "points": 20, "field": "ergonomic_features"},
                    {"keyword": "tilt", "points": 10, "field": "ergonomic_features"},
                    {"keyword": "negative tilt", "points": 10, "field": "ergonomic_features"},
                    {"keyword": "wrist rest", "points": 10, "field": "ergonomic_features"},
                    {"keyword": "palm", "points": 10, "field": "ergonomic_features"},
                    {"keyword": "contour", "points": 15, "field": "ergonomic_features"},
                    {"keyword": "thumb", "points": 10, "field": "ergonomic_features"},
                    {"keyword": "ortholinear", "points": 5, "field": "ergonomic_features"},
                    {"keyword": "columnar", "points": 5, "field": "ergonomic_features"},
                ],
            ),
            ScoringDimension(
                name="reviews",
                weight=0.20,
                display_name="Reviews",
                scoring_type="formula_reviews",
                description="Rating average and review count.",
            ),
            ScoringDimension(
                name="value",
                weight=0.20,
                display_name="Value",
                scoring_type="formula_value",
                description="Lower price = higher score.",
            ),
            ScoringDimension(
                name="build",
                weight=0.20,
                display_name="Build",
                scoring_type="keyword",
                description="Build quality signals: mechanical, hot-swap, firmware, wireless, materials.",
                rules=[
                    {"keyword": "membrane", "points": -30, "field": "switch_type"},
                    {"keyword": "hot_swappable:true", "points": 25, "field": "__bool__hot_swappable"},
                    {"keyword": "qmk", "points": 30, "field": "programmable"},
                    {"keyword": "via", "points": 30, "field": "programmable"},
                    {"keyword": "zmk", "points": 30, "field": "programmable"},
                    {"keyword": "bluetooth", "points": 15, "field": "connectivity"},
                    {"keyword": "2.4", "points": 15, "field": "connectivity"},
                    {"keyword": "cherry", "points": 15, "field": "switch_brand"},
                    {"keyword": "kailh", "points": 15, "field": "switch_brand"},
                    {"keyword": "gateron", "points": 15, "field": "switch_brand"},
                    {"keyword": "aluminum", "points": 15, "field": "ergonomic_features"},
                ],
            ),
        ],
        category_fields=[
            "layout_size", "switch_type", "switch_brand", "hot_swappable",
            "connectivity", "programmable", "ergonomic_features",
        ],
        preference_fields=[
            "brand", "product_title", "ergonomic_features", "switch_type",
            "switch_brand", "programmable", "connectivity", "category",
        ],
    )


_LLM_PROMPT = """\
You are a product scoring expert. Given a search query, generate a scoring profile \
that determines how to evaluate and rank products in that category.

Search query: "{query}"

Return a JSON object with this exact structure:
{{
  "category": "<short category name>",
  "dimensions": [
    {{
      "name": "<snake_case identifier>",
      "weight": <float 0.0-1.0>,
      "display_name": "<Human Readable Name>",
      "scoring_type": "<keyword | formula_reviews | formula_value>",
      "description": "<what this dimension measures>",
      "rules": [
        {{"keyword": "<term to find>", "points": <int>, "field": "<product field to search>"}}
      ]
    }}
  ],
  "category_fields": ["<field1>", "<field2>"],
  "preference_fields": ["<field1>", "<field2>"]
}}

Rules:
- 3-6 dimensions total
- Weights MUST sum to 1.0
- Exactly ONE dimension must have scoring_type "formula_reviews" (scores based on \
rating_avg and rating_count)
- Exactly ONE dimension must have scoring_type "formula_value" (scores based on \
price_usd — lower price = higher score)
- Remaining dimensions use scoring_type "keyword" with rules
- For keyword rules, "field" can be any Product field: product_title, brand, \
ergonomic_features, switch_type, connectivity, programmable, category, or \
"extra.<key>" for data in the extra dict
- For keyword rules, "points" can be negative (penalties) or positive (bonuses), \
typically -30 to +30
- Each keyword dimension is scored 0-100 (clamped)
- "category_fields" lists the most important Product fields for this category
- "preference_fields" lists fields to search when matching user preference keywords \
(always include brand, product_title, category)

Return ONLY the JSON object, no other text.
"""


def _parse_profile_json(raw: dict) -> ScoringProfile:
    """Parse and normalize a profile from raw JSON dict."""
    dims = []
    for d in raw.get("dimensions", []):
        dims.append(ScoringDimension(
            name=d["name"],
            weight=float(d["weight"]),
            display_name=d.get("display_name", d["name"].replace("_", " ").title()),
            scoring_type=d["scoring_type"],
            description=d.get("description", ""),
            rules=d.get("rules", []),
        ))

    # Normalize weights to sum to 1.0
    total_weight = sum(d.weight for d in dims)
    if total_weight > 0 and abs(total_weight - 1.0) > 0.01:
        for d in dims:
            d.weight = d.weight / total_weight

    return ScoringProfile(
        category=raw.get("category", "unknown"),
        dimensions=dims,
        category_fields=raw.get("category_fields", []),
        preference_fields=raw.get("preference_fields", ["brand", "product_title", "category"]),
    )


def generate_profile_from_llm(query: str) -> ScoringProfile | None:
    """Call Claude API (Sonnet) to generate a scoring profile for the query.

    Returns None if no API key is set, the anthropic package is missing, or the
    LLM call fails for any reason.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.debug("No ANTHROPIC_API_KEY set, skipping LLM profile generation")
        return None

    try:
        import anthropic
    except ImportError:
        logger.debug("anthropic package not installed, skipping LLM profile generation")
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": _LLM_PROMPT.format(query=query)},
            ],
        )
        text = message.content[0].text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text[: text.rfind("```")]
        raw = json.loads(text)
        profile = _parse_profile_json(raw)
        logger.info(
            "LLM generated scoring profile for '%s': %d dimensions (%s)",
            query,
            len(profile.dimensions),
            ", ".join(d.name for d in profile.dimensions),
        )
        return profile
    except Exception:
        logger.warning("LLM profile generation failed, will use fallback", exc_info=True)
        return None


def get_scoring_profile(query: str) -> ScoringProfile:
    """Main entry point: try LLM profile, fall back to keyboard profile."""
    profile = generate_profile_from_llm(query)
    if profile is not None:
        return profile
    logger.info("Using default keyboard scoring profile")
    return get_keyboard_profile()
