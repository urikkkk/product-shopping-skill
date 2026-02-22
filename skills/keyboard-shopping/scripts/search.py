#!/usr/bin/env python3
"""OpenClaw skill entry point for keyboard shopping.

Wraps the keyboard-shopping-agent pipeline with a shopping-expert-compatible CLI
that outputs to stdout as text (markdown) or JSON.

Usage:
    python skills/keyboard-shopping/scripts/search.py "ergonomic split keyboard" --mode seed --output text
    python skills/keyboard-shopping/scripts/search.py "mechanical keyboard" --budget "$200" --output json
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# Ensure the repo root is importable when invoked directly
_repo_root = str(Path(__file__).resolve().parents[3])
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from src.adapters import get_adapter
from src.enrichment import enrich_top_products
from src.filters import apply_filters
from src.output_formats import format_json, format_text
from src.preferences import apply_preferences
from src.schema import normalize_price
from src.scoring import rank_products


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="keyboard-shopping",
        description="Search, score, and compare ergonomic keyboards across retailers.",
    )
    parser.add_argument(
        "query", nargs="?", default="ergonomic mechanical keyboard",
        help="Search query (default: 'ergonomic mechanical keyboard')",
    )
    parser.add_argument(
        "--mode", choices=["online", "seed", "auto"], default="auto",
        help="Data source mode (default: auto)",
    )
    parser.add_argument("--budget", default=None, help='Max budget (e.g. "$200" or 200)')
    parser.add_argument(
        "--max-results", type=int, default=10, help="Number of top results (default: 10)"
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--preferences", default=None,
        help="Comma-separated preference keywords to boost (e.g. 'Keychron, split, QMK')",
    )
    parser.add_argument("--wireless", choices=["yes", "no"], default=None, help="Filter wireless")
    parser.add_argument("--layout", default=None, help="Filter by layout (split, alice, ortho)")
    parser.add_argument("--location", default="11201", help="Shipping ZIP code (default: 11201)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stderr)

    budget = normalize_price(args.budget) if args.budget else None
    start = time.time()

    # Collect from all adapters
    all_products = []
    adapter_names = ["amazon", "bestbuy", "walmart"]
    for name in adapter_names:
        try:
            adapter = get_adapter(name, mode=args.mode)
            products = adapter.search(
                query=args.query,
                zip_code=args.location,
                max_results=100,
            )
            all_products.extend(products)
        except Exception as exc:
            print(f"Warning: {name} adapter failed: {exc}", file=sys.stderr)

    if not all_products:
        error = {"error": "No products collected. Check adapter configuration."}
        if args.output == "json":
            import json
            print(json.dumps(error, indent=2))
        else:
            print("Error: No products collected. Check adapter configuration.")
        return 1

    # Filter
    filtered = apply_filters(
        all_products, budget=budget, wireless=args.wireless, layout=args.layout,
    )

    # Rank
    ranked = rank_products(filtered, top_n=args.max_results)

    # Apply preferences
    if args.preferences:
        ranked = apply_preferences(ranked, args.preferences)

    # Enrich
    top_products = [p for p, _ in ranked]
    reviews = enrich_top_products(top_products)

    elapsed = time.time() - start

    metadata = {
        "query": args.query,
        "mode": args.mode,
        "budget": budget,
        "adapters": adapter_names,
        "elapsed_seconds": round(elapsed, 1),
        "total_collected": len(all_products),
        "total_filtered": len(filtered),
    }

    if args.output == "json":
        print(format_json(ranked, reviews, metadata))
    else:
        print(format_text(ranked, reviews, metadata))

    return 0


if __name__ == "__main__":
    sys.exit(main())
