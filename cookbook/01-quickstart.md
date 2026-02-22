# Quickstart: Run Locally in 5 Minutes

## Prerequisites

- Python 3.10 or later
- pip (comes with Python)

## Step 1: Clone the repo

```bash
git clone https://github.com/urikkkk/keyboard-shopping-agent.git
cd keyboard-shopping-agent
```

## Step 2: Install dependencies

```bash
pip install -e .
```

Or with a virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
pip install -e .
```

## Step 3: Run the pipeline

```bash
python -m scripts.run_pipeline --zip 11201 --out xlsx
```

This will:
1. Collect products from Amazon, Best Buy, and Walmart seed datasets
2. Score and rank the top 10
3. Enrich the top 10 with professional review summaries
4. Output `output/ergonomic_keyboards.xlsx` and `output/keyboards.csv`

## Step 4: Open the web app

```bash
open web/keyboard_finder.html
# Or on Linux: xdg-open web/keyboard_finder.html
```

## Step 5: Try different options

```bash
# Filter to wireless keyboards under $300
python -m scripts.run_pipeline --zip 11201 --budget 300 --wireless yes

# Only split layout keyboards
python -m scripts.run_pipeline --zip 11201 --layout split

# Dry run (see what would happen without writing files)
python -m scripts.run_pipeline --dry-run

# Verbose output
python -m scripts.run_pipeline --zip 11201 -v
```

## What's next?

- Add your own data: [How to add a new retailer adapter](04-add-retailer-adapter.md)
- Use real APIs: [How to add API keys](03-api-keys.md)
- Output to Google Sheets: [Google Sheets setup](02-google-sheets-credentials.md)
- Customize scoring: [How scoring works](05-scoring.md)
