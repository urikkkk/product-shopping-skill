# Create Your Own Personalized Google Shops (Open Source)

**10x Better, More Accurate, Tailored to Your Needs, No Sponsored Links**

---

An open-source pipeline that searches multiple retailers, normalizes product data into a single schema, scores and ranks results using a transparent algorithm, enriches the top picks with professional review summaries, and outputs everything to a spreadsheet and interactive web app.

**No ads. No sponsored links. No tracking. Just the best products for _you_.**

Currently focused on ergonomic and mechanical keyboards. Supports 13+ retailers via Nimble (Amazon, Walmart, Target, B&H, Home Depot, and more), plus direct integrations with Best Buy and Walmart APIs. Designed to be extended to any product category and any retailer.

## Why this exists

Google Shopping is full of sponsored listings. Affiliate sites bury real recommendations under SEO-optimized fluff. You deserve a shopping tool that:

- Shows **every option**, not just the ones that pay for placement
- Ranks products on **what matters to you** (ergonomics, build quality, value, real reviews)
- Gives you **professional review summaries** instead of making you open 20 tabs
- Runs **locally on your machine** — your data, your preferences, no tracking
- Is **fully transparent** — every scoring weight and decision is in the code

## What it does

```
Retailers (Amazon, Best Buy, Walmart, BYO CSV)
  |
  v
Normalize -> Score & Rank -> Enrich with Pro Reviews -> Output
  |                                                        |
  v                                                        v
Unified schema                              XLSX / CSV / Google Sheets
(all products)                                      +
                                              Web App (interactive)
```

1. **Collects** products from 13+ retailers via Nimble, or 3 retailers with seed data
2. **Normalizes** everything into a unified schema with 20+ fields
3. **Scores** on 4 dimensions: ergonomics (40%), reviews (20%), value (20%), build (20%)
4. **Ranks** the top 10 with transparent score breakdowns
5. **Enriches** the top 10 with professional review summaries (pros, cons, verdict)
6. **Outputs** a styled XLSX (3 tabs), CSV, and optional Google Sheets
7. **Serves** an interactive web app for filtering and recommendations

## Install as OpenClaw / ClawdBot Skill

This project is packaged as an [OpenClaw](https://docs.openclaw.ai/tools/skills) skill, so AI agents can install and invoke it directly.

### Option 1: Install from ClawHub (recommended)

```bash
clawhub install product-shopping
```

### Option 2: Install from GitHub

```bash
# Clone into your OpenClaw skills directory
git clone https://github.com/urikkkk/product-shopping-skill.git ~/clawd/skills/product-shopping
```

Or, if you're using a custom skills path:

```bash
git clone https://github.com/urikkkk/product-shopping-skill.git /path/to/your/skills/product-shopping
```

### Option 3: Ask your agent

Paste this into your OpenClaw / ClawdBot chat:

> Install the product-shopping skill from https://github.com/urikkkk/product-shopping-skill

The agent will handle cloning, dependency installation, and configuration.

### Verify installation

```bash
# Check the skill is recognized
openclaw skills list --eligible

# Quick test (uses seed data, no API keys needed)
python skills/product-shopping/scripts/search.py "ergonomic keyboard" --mode seed --output text
```

### Skill invocation

Once installed, the skill accepts a search query and returns ranked results to stdout:

```bash
# Text output (markdown table)
python skills/product-shopping/scripts/search.py "ergonomic keyboard" --mode seed --output text

# JSON output (structured, for downstream agents)
python skills/product-shopping/scripts/search.py "mechanical keyboard" --mode seed --budget "$200" --output json

# With preference boosting
python skills/product-shopping/scripts/search.py "keyboard" --mode seed --preferences "Keychron, split, QMK" --output text
```

See [`skills/product-shopping/SKILL.md`](skills/product-shopping/SKILL.md) for the full flag reference.

### Optional: Live data with Nimble (recommended)

The skill works out of the box with curated seed data (`--mode seed`). For live data from **13+ retailers with a single API key**, set up Nimble:

```bash
export NIMBLE_API_KEY="your-nimble-api-key"
```

Nimble dynamically discovers all available e-commerce SERP templates at runtime, so new retailers are picked up automatically. Currently supported retailers:

| Retailer | Template |
|----------|----------|
| Amazon | `amazon_serp` |
| Walmart | `walmart_serp` |
| Target | `target_serp` |
| B&H | `b_and_h_serp` |
| Home Depot | `homedepot_serp` |
| Staples | `staples_serp` |
| Office Depot | `office_depot_serp` |
| ASOS | `asos_serp` |
| Foot Locker | `footlocker_serp` |
| Kroger | `kroger_serp` |
| Slickdeals | `slickdeals_serp` |
| Sam's Club | `sams_club_plp` |
| Walmart Canada | `walmart_ca_serp` |

Then use `--mode online` or `--mode auto` (auto uses APIs when keys are present, falls back to seed).

### Alternative: Individual retailer API keys

You can also use individual retailer APIs instead of or alongside Nimble:

| Variable | Retailer | How to get it |
|----------|----------|---------------|
| `BESTBUY_API_KEY` | Best Buy | Free at [developer.bestbuy.com](https://developer.bestbuy.com/) |
| `AMAZON_ACCESS_KEY`, `AMAZON_SECRET_KEY`, `AMAZON_PARTNER_TAG` | Amazon | [PA-API 5.0](https://webservices.amazon.com/paapi5/documentation/) |
| `WALMART_API_KEY` | Walmart | [Walmart Affiliate API](https://developer.walmart.com/) |

---

## Quickstart (standalone CLI)

```bash
git clone https://github.com/urikkkk/product-shopping-skill.git
cd product-shopping-skill
pip install -e .
python -m scripts.run_pipeline --zip 11201 --out xlsx
```

Then open the web app:

```bash
open web/keyboard_finder.html
```

That's it. You have a ranked spreadsheet and an interactive recommender.

See the [full quickstart guide](cookbook/01-quickstart.md) for more options.

## CLI usage

```bash
# Basic run — outputs XLSX + CSV
python -m scripts.run_pipeline --zip 11201 --out xlsx

# Text output to stdout (for piping to other tools)
python -m scripts.run_pipeline --out text --mode seed

# JSON output to stdout
python -m scripts.run_pipeline --out json --mode seed --budget 200

# Filter to wireless keyboards under $300
python -m scripts.run_pipeline --zip 11201 --budget 300 --wireless yes

# With preference boosting
python -m scripts.run_pipeline --mode seed --preferences "Keychron, split"

# Only split layout, minimum 100 reviews
python -m scripts.run_pipeline --zip 11201 --layout split --min-rating-count 100

# Output to Google Sheets
python -m scripts.run_pipeline --zip 11201 --out google_sheets

# Bring your own data (CSV)
python -m scripts.run_pipeline --csv-file my_keyboards.csv

# Dry run (show plan, don't write files)
python -m scripts.run_pipeline --dry-run

# Verbose logging
python -m scripts.run_pipeline --zip 11201 -v
```

## Architecture

```
product-shopping-skill/
  src/
    schema.py           # Unified Product dataclass + normalization
    scoring.py          # 4-dimension scoring engine
    output.py           # XLSX, CSV, Google Sheets writers
    output_formats.py   # Text (markdown) and JSON stdout formatters
    filters.py          # Product filtering (budget, wireless, layout)
    preferences.py      # Preference-based ranking boost
    adapters/
      base.py           # BaseAdapter with throttling, retry, mode control
      amazon_adapter.py # Amazon (PA-API or seed data)
      bestbuy_adapter.py# Best Buy (Products API or seed data)
      walmart_adapter.py# Walmart (Affiliate API or seed data)
      nimble_adapter.py # Nimble WSA (13+ retailers via dynamic discovery)
      csv_adapter.py    # BYO CSV data loader
    enrichment/
      reviews.py        # Professional review database
  scripts/
    run_pipeline.py     # CLI entry point
  skills/
    product-shopping/   # OpenClaw skill packaging
      SKILL.md          # Skill manifest with YAML frontmatter
      _meta.json        # Skill metadata
      scripts/
        search.py       # Skill entry point (stdout output)
  web/
    keyboard_finder.html# Interactive web app (self-contained)
  data/
    sample_keyboards.csv# Sample dataset (10 rows)
    schema.json         # JSON Schema for product records
  cookbook/              # Step-by-step guides
  docs/                 # Architecture docs + screenshot placeholders
  tests/                # pytest test suite (101 tests)
```

See [docs/architecture.md](docs/architecture.md) for a detailed system overview.

## Scoring

Every product is scored on four dimensions:

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Ergonomics | 40% | Split, tenting, tilt, contoured keywells, thumb clusters |
| Reviews | 20% | Rating average + review count |
| Value | 20% | Price-to-feature ratio |
| Build Quality | 20% | Mechanical switch, hot-swap, QMK/VIA, wireless, materials |

All weights and scoring logic are in [`src/scoring.py`](src/scoring.py) and
fully customizable. See [How scoring works](cookbook/05-scoring.md).

## Web app

The interactive recommender lets you:

- Set a **budget slider** ($30–$550)
- Filter by **layout** (split, alice, ortholinear, wave, low-profile)
- Filter by **connectivity** (wireless / wired)
- Filter by **hot-swap** and **mechanical only**
- Filter by **store**
- Sort by **score, price, or rating**
- See a **"Top Pick for You"** recommendation that updates in real-time
- Click through to **buy directly** — no affiliate links, no middleman

## Cookbook

| Guide | Description |
|-------|-------------|
| [Quickstart](cookbook/01-quickstart.md) | Run locally in 5 minutes |
| [Google Sheets](cookbook/02-google-sheets-credentials.md) | Set up Google Sheets output |
| [API Keys](cookbook/03-api-keys.md) | Add Best Buy / Walmart / Amazon API keys |
| [New Adapter](cookbook/04-add-retailer-adapter.md) | Add a new retailer source |
| [Scoring](cookbook/05-scoring.md) | Understand and customize scoring |
| [Deploy Web App](cookbook/06-deploy-web-app.md) | Deploy to GitHub Pages |

## Extending to other products

This repo is focused on keyboards, but the architecture is product-agnostic:

1. Fork the repo
2. Update the `Product` schema in `src/schema.py` for your category
3. Update scoring dimensions in `src/scoring.py`
4. Add/modify adapters for your target retailers
5. Update the web app UI

Example categories that would work well:
- Standing desks
- Ergonomic mice
- Monitors
- Office chairs
- Headphones

## Roadmap

- [ ] **Live API integrations** — Best Buy API is free; Walmart and Amazon need approval
- [ ] **More retailers** — Newegg, B&H, direct manufacturer stores
- [ ] **Price history tracking** — Watch prices over time, alert on drops
- [ ] **AI-powered review analysis** — Use an LLM to summarize hundreds of user reviews
- [ ] **Comparison view** — Side-by-side product comparison in the web app
- [ ] **Browser extension** — See scores while browsing retailer sites
- [ ] **Multi-category support** — Mice, monitors, desks, chairs
- [ ] **Community scoring presets** — Share and vote on scoring configurations

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

The easiest ways to contribute:
- **Add a retailer adapter** — follow the [cookbook guide](cookbook/04-add-retailer-adapter.md)
- **Improve scoring** — propose weight changes or new dimensions
- **Add product data** — submit CSV files with products from new stores
- **Improve the web app** — better filtering, comparison view, mobile UI
- **Write tests** — increase coverage for adapters and scoring edge cases

## Legal & safety

- **Respect Terms of Service.** This tool prefers official APIs. Direct scraping is intentionally not implemented for retailers that prohibit it.
- **Rate limiting.** All adapters include built-in request throttling.
- **Your responsibility.** Users are responsible for complying with each retailer's ToS and applicable laws.
- **No affiliate links.** Product URLs are direct links to retailer pages. We don't earn commissions.
- **No data collection.** The pipeline runs entirely on your machine. No data is sent anywhere.

## License

[MIT](LICENSE) — use it however you want.
