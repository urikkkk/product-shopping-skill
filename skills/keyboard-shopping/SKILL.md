---
name: keyboard-shopping
description: Finds, scores, and compares ergonomic and mechanical keyboards across retailers with transparent 4-dimension scoring
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
        package: keyboard-shopping-agent
        bins: [uv]
---

# keyboard-shopping

Search, score, and compare ergonomic and mechanical keyboards across Amazon, Best Buy, and Walmart.

## How to Invoke

```bash
python skills/keyboard-shopping/scripts/search.py "<query>" [options]
```

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `query` (positional) | Search query | `"ergonomic mechanical keyboard"` |
| `--mode` | `online` (API), `seed` (curated), `auto` | `auto` |
| `--budget` | Max price, e.g. `"$200"` or `200` | None |
| `--max-results` | Number of top results to return | `10` |
| `--output` | Output format: `text` or `json` | `text` |
| `--preferences` | Comma-separated boost keywords | None |
| `--wireless` | Filter: `yes` or `no` | None |
| `--layout` | Filter by layout: `split`, `alice`, `ortho` | None |
| `--location` | Shipping ZIP code | `11201` |

## Output Formats

### Text (`--output text`)
Returns a markdown table with columns: Rank, Product, Brand, Price, Score, Ergonomics, Review, Value, Build, Store. Includes a pro reviews section and scoring weight footer.

### JSON (`--output json`)
Returns structured JSON with two top-level keys:
- `metadata`: query, mode, budget, adapters used, timing, scoring weights
- `results`: array of ranked products with full score breakdown and pro reviews

## Scoring System

Products are scored 0-100 across 4 weighted dimensions:
- **Ergonomics (40%)**: Split, tented, contoured, thumb clusters, etc.
- **Reviews (20%)**: Rating average + review count
- **Value (20%)**: Price-to-quality ratio (lower price = higher score)
- **Build Quality (20%)**: Hot-swap, QMK/VIA, wireless, switch brand, materials

## Data Sources

- **Seed mode** (no API keys needed): Curated database of 23 real products across 3 retailers
- **Online mode**: Amazon PA-API 5.0, Best Buy Products API v1, Walmart Affiliate API

## Examples

```bash
# Basic search with seed data (no API keys needed)
python skills/keyboard-shopping/scripts/search.py "ergonomic split keyboard" --mode seed --output text

# Budget-constrained JSON output
python skills/keyboard-shopping/scripts/search.py "mechanical keyboard" --mode seed --budget "$200" --output json --max-results 5

# With preference boosting
python skills/keyboard-shopping/scripts/search.py "keyboard" --mode seed --preferences "Keychron, split, QMK" --output text

# Filter for wireless split keyboards
python skills/keyboard-shopping/scripts/search.py "keyboard" --mode seed --wireless yes --layout split --output json
```
