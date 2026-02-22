"""CLI entry point for the keyboard shopping pipeline.

Usage:
    python -m scripts.run_pipeline --zip 11201 --out xlsx
    python -m scripts.run_pipeline --zip 11201 --out google_sheets --sheet-id YOUR_SHEET_ID
    python -m scripts.run_pipeline --dry-run
"""

from __future__ import annotations

import argparse
import logging
import sys
import time

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from src.adapters import get_adapter, list_adapters
from src.enrichment import enrich_top_products
from src.output import write_csv, write_google_sheets, write_xlsx
from src.schema import Product
from src.scoring import ScoreBreakdown, rank_products

console = Console()


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="keyboard-shopping-agent",
        description=(
            "Personalized keyboard shopping pipeline. "
            "Gathers products from multiple retailers, scores them, "
            "enriches top picks with pro reviews, and outputs results."
        ),
    )
    parser.add_argument("--zip", default="11201", help="Shipping ZIP code (default: 11201)")
    parser.add_argument(
        "--target", type=int, default=100, help="Target number of products to collect"
    )
    parser.add_argument(
        "--query", default="ergonomic mechanical keyboard", help="Search query"
    )
    parser.add_argument(
        "--out",
        choices=["xlsx", "csv", "google_sheets", "all"],
        default="xlsx",
        help="Output format (default: xlsx)",
    )
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--sheet-id", default=None, help="Google Sheet ID (for sheets output)")
    parser.add_argument("--top-n", type=int, default=10, help="Number of top picks (default: 10)")

    # Filters
    parser.add_argument("--budget", type=float, default=None, help="Max budget in USD")
    parser.add_argument("--wireless", choices=["yes", "no"], default=None, help="Filter wireless")
    parser.add_argument("--layout", default=None, help="Filter by layout (split, alice, ortho)")
    parser.add_argument("--max-price", type=float, default=None, help="Alias for --budget")
    parser.add_argument("--min-rating-count", type=int, default=0, help="Min review count")

    # Modes
    parser.add_argument(
        "--adapters",
        nargs="+",
        default=["amazon", "bestbuy", "walmart"],
        help=f"Adapters to use (available: {', '.join(list_adapters())})",
    )
    parser.add_argument("--csv-file", default=None, help="Path to BYO CSV file (adds csv adapter)")
    parser.add_argument("--use-api", action="store_true", help="Prefer API mode for adapters")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    return parser.parse_args(argv)


def apply_filters(products: list[Product], args: argparse.Namespace) -> list[Product]:
    """Apply user-specified filters."""
    budget = args.budget or args.max_price
    filtered = products

    if budget:
        filtered = [p for p in filtered if p.price_usd <= budget]

    if args.wireless == "yes":
        filtered = [
            p for p in filtered
            if any(kw in p.connectivity.lower() for kw in ("bluetooth", "2.4"))
        ]
    elif args.wireless == "no":
        filtered = [
            p for p in filtered
            if not any(kw in p.connectivity.lower() for kw in ("bluetooth", "2.4"))
        ]

    if args.layout:
        layout_kw = args.layout.lower()
        filtered = [
            p for p in filtered
            if layout_kw in p.layout_size.lower() or layout_kw in p.category.lower()
        ]

    if args.min_rating_count:
        filtered = [p for p in filtered if p.rating_count >= args.min_rating_count]

    return filtered


def print_summary(
    top10: list[tuple[Product, ScoreBreakdown]],
    total_products: int,
):
    """Print a rich summary table."""
    table = Table(title=f"Top {len(top10)} Ergonomic Keyboards (of {total_products} total)")
    table.add_column("#", style="bold", width=3)
    table.add_column("Product", style="cyan", max_width=35)
    table.add_column("Brand", width=12)
    table.add_column("Price", style="green", width=8)
    table.add_column("Rating", width=8)
    table.add_column("Score", style="bold yellow", width=7)
    table.add_column("Store", width=12)

    for i, (p, s) in enumerate(top10, 1):
        table.add_row(
            str(i),
            p.product_title,
            p.brand,
            f"${p.price_usd:.0f}",
            f"{p.rating_avg}/5",
            f"{s.total}",
            p.source_site,
        )

    console.print(table)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    console.print(
        "\n[bold]Keyboard Shopping Agent[/bold] v0.1.0\n"
        f"  ZIP: {args.zip}  |  Query: {args.query}  |  Output: {args.out}\n"
        f"  Adapters: {', '.join(args.adapters)}\n"
    )

    if args.dry_run:
        console.print("[yellow]DRY RUN[/yellow] — showing plan only, no output will be written.\n")
        console.print(f"  Would search: {', '.join(args.adapters)}")
        console.print(f"  Target: ~{args.target} products")
        console.print(f"  Filters: budget={args.budget}, wireless={args.wireless}, "
                      f"layout={args.layout}")
        console.print(f"  Output: {args.out} -> {args.output_dir}/")
        return

    # ── Step 1: Collect ──────────────────────────────────────────────────────
    console.print("[bold]Step 1:[/bold] Collecting products...")
    start = time.time()
    all_products: list[Product] = []

    adapter_names = list(args.adapters)
    if args.csv_file:
        adapter_names.append("csv")

    for name in adapter_names:
        try:
            kwargs = {}
            if name == "csv":
                kwargs["file_path"] = args.csv_file
            adapter = get_adapter(name, **kwargs)
            products = adapter.search(
                query=args.query,
                zip_code=args.zip,
                max_results=args.target,
            )
            console.print(f"  [{name}] {len(products)} products")
            all_products.extend(products)
        except Exception:
            logger.exception("Adapter '%s' failed", name)

    elapsed = time.time() - start
    console.print(f"  Total: {len(all_products)} products in {elapsed:.1f}s\n")

    if not all_products:
        console.print("[red]No products collected. Check adapter configuration.[/red]")
        sys.exit(1)

    # ── Step 2: Filter ───────────────────────────────────────────────────────
    filtered = apply_filters(all_products, args)
    if len(filtered) < len(all_products):
        console.print(f"[bold]Step 2:[/bold] Filtered to {len(filtered)} products\n")
    else:
        console.print(f"[bold]Step 2:[/bold] No filters applied ({len(filtered)} products)\n")

    # ── Step 3: Rank ─────────────────────────────────────────────────────────
    console.print(f"[bold]Step 3:[/bold] Ranking top {args.top_n}...")
    top10 = rank_products(filtered, top_n=args.top_n)
    print_summary(top10, len(filtered))

    # ── Step 4: Enrich ───────────────────────────────────────────────────────
    console.print(f"\n[bold]Step 4:[/bold] Enriching top {len(top10)} with professional reviews...")
    top_products = [p for p, _ in top10]
    reviews = enrich_top_products(top_products)
    enriched_count = sum(1 for revs in reviews.values() if revs)
    console.print(f"  Found reviews for {enriched_count}/{len(top10)} products\n")

    # ── Step 5: Output ───────────────────────────────────────────────────────
    console.print(f"[bold]Step 5:[/bold] Writing output ({args.out})...")

    if args.out in ("xlsx", "all"):
        xlsx_path = write_xlsx(filtered, top10, reviews, output_dir=args.output_dir)
        console.print(f"  XLSX: {xlsx_path}")

    if args.out in ("csv", "all", "xlsx"):
        csv_path = write_csv(filtered, output_dir=args.output_dir)
        console.print(f"  CSV:  {csv_path}")

    if args.out in ("google_sheets", "all"):
        try:
            url = write_google_sheets(filtered, top10, reviews, sheet_id=args.sheet_id)
            console.print(f"  Sheet: {url}")
        except Exception:
            logger.exception("Google Sheets output failed")
            console.print("  [yellow]Google Sheets failed — falling back to XLSX[/yellow]")
            xlsx_path = write_xlsx(filtered, top10, reviews, output_dir=args.output_dir)
            console.print(f"  XLSX: {xlsx_path}")

    console.print("\n[bold green]Done![/bold green]\n")


if __name__ == "__main__":
    main()
