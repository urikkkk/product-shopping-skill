---
name: product-shopping
description: Searches, scores, and compares products across multiple retailers with transparent multi-dimension scoring
version: 0.1.0
metadata:
  openclaw:
    requires:
      bins: [uv]
      env: []
    optionalEnv:
      - BESTBUY_API_KEY
      - AMAZON_ACCESS_KEY
      - AMAZON_SECRET_KEY
      - AMAZON_PARTNER_TAG
      - WALMART_API_KEY
    install:
      - kind: uv
        package: product-shopping-skill
        bins: [uv]
---

# product-shopping

Search, score, and compare products across Amazon, Best Buy, and Walmart. Returns ranked results with transparent multi-dimension scoring, professional review summaries, and structured output for downstream consumption by AI agents.

Currently supports **keyboards** as the first product category, with ergonomics-aware scoring. Additional categories can be added by extending the adapter and scoring modules.

## How to Invoke

```bash
python skills/product-shopping/scripts/search.py "<query>" [options]
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `query` (positional) | Search query | `"ergonomic mechanical keyboard"` |
| `--mode` | `online` (API), `seed` (curated data), `auto` | `auto` |
| `--budget` | Max price, e.g. `"$200"` or `200` | None |
| `--max-results` | Number of top results to return | `10` |
| `--output` | Output format: `text` or `json` | `text` |
| `--preferences` | Comma-separated boost keywords | None |
| `--wireless` | Filter: `yes` or `no` | None |
| `--layout` | Filter by layout keyword | None |
| `--location` | Shipping ZIP code | `11201` |

## Output Formats

### Text (`--output text`)
Returns a markdown table with columns: Rank, Product, Brand, Price, Score, plus per-dimension scores and Store. Includes a professional reviews section and scoring weight footer.

### JSON (`--output json`)
Returns structured JSON with two top-level keys:
- `metadata`: query, mode, budget, adapters used, timing, scoring weights
- `results`: array of ranked products with full score breakdown and professional reviews

## Scoring System

Products are scored 0-100 across 4 weighted dimensions:
- **Ergonomics (40%)**: Category-specific feature scoring
- **Reviews (20%)**: Rating average + review count
- **Value (20%)**: Price-to-quality ratio (lower price = higher score)
- **Build Quality (20%)**: Materials, features, and brand quality signals

## Data Sources

- **Seed mode** (no API keys needed): Curated product database across 3 retailers
- **Online mode**: Amazon PA-API 5.0, Best Buy Products API v1, Walmart Affiliate API

## Examples

```bash
# Basic search with seed data (no API keys needed)
python skills/product-shopping/scripts/search.py "ergonomic split keyboard" --mode seed --output text

# Budget-constrained JSON output
python skills/product-shopping/scripts/search.py "mechanical keyboard" --mode seed --budget "$200" --output json --max-results 5

# With preference boosting
python skills/product-shopping/scripts/search.py "keyboard" --mode seed --preferences "Keychron, split, QMK" --output text

# Filter for wireless products
python skills/product-shopping/scripts/search.py "keyboard" --mode seed --wireless yes --output json
```
