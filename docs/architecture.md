# Architecture

## System overview

```
                    +-----------+
                    |   CLI     |  scripts/run_pipeline.py
                    +-----+-----+
                          |
              +-----------+-----------+
              |           |           |
         +----v---+  +----v---+  +---v----+
         | Amazon |  |BestBuy |  |Walmart |  src/adapters/
         +----+---+  +----+---+  +---+----+
              |           |           |       (+ CSV BYO adapter)
              +-----+-----+-----+----+
                    |
              +-----v-----+
              |  Product   |  src/schema.py
              |  Schema    |  Unified normalized records
              +-----+------+
                    |
              +-----v------+
              |  Scoring    |  src/scoring.py
              |  Engine     |  Ergo / Review / Value / Build
              +-----+------+
                    |
              +-----v------+
              | Enrichment  |  src/enrichment/reviews.py
              | (Top N)     |  Professional review summaries
              +-----+------+
                    |
          +---------+---------+
          |         |         |
     +----v---+ +---v---+ +--v-----------+
     |  XLSX  | |  CSV  | | Google Sheets|  src/output.py
     +--------+ +---+---+ +--------------+
                    |
              +-----v------+
              |  Web App    |  web/keyboard_finder.html
              |  (static)   |  Loads CSV, filters, recommends
              +-------------+
```

## Data flow

1. **Collect**: Each adapter searches its retailer and returns `Product` objects.
   Adapters support API mode (if keys provided) or seed/BYO mode.

2. **Normalize**: All products conform to the `Product` dataclass schema.
   Prices, ratings, and booleans are normalized during ingestion.

3. **Filter**: User-specified filters (budget, wireless, layout) are applied.

4. **Score & Rank**: The scoring engine computes a composite score across
   four weighted dimensions. Products are deduplicated (best price wins)
   and ranked.

5. **Enrich**: The top N products are enriched with professional review
   summaries from a curated database.

6. **Output**: Results are written to XLSX (3 tabs), CSV, and/or Google Sheets.

7. **Web App**: A self-contained HTML file loads the product data and provides
   an interactive filtering/recommendation UI.

## Design decisions

### Why seed data instead of scraping?

- Scraping Amazon/Walmart violates their ToS
- API access requires approval and has rate limits
- Seed data provides immediate value out of the box
- Users can bring their own data via CSV adapter

### Why a single HTML file for the web app?

- Zero dependencies, zero build step
- Can be deployed anywhere (GitHub Pages, S3, local file)
- All data is embedded — works offline
- Easy to customize (it's just HTML + CSS + JS)

### Why weighted composite scoring?

- Single-number ranking is intuitive
- Weights make priorities transparent and adjustable
- Each dimension is independently testable
- Users can customize weights for their needs
