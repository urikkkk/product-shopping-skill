# How to Add API Keys for Best Buy / Walmart / Amazon

By default, the pipeline uses curated seed datasets. For live data, you can
configure API keys for each retailer.

## Best Buy (free, easy)

1. Sign up at [developer.bestbuy.com](https://developer.bestbuy.com/)
2. Create an app to get an API key
3. Set the environment variable:

```bash
export BESTBUY_API_KEY="your_key_here"
```

The Best Buy adapter will automatically use the Products API when this key
is present.

## Walmart

1. Apply for the [Walmart Affiliate API](https://developer.walmart.com/)
2. Once approved, get your access token
3. Set the environment variable:

```bash
export WALMART_API_KEY="your_token_here"
```

## Amazon (PA-API 5.0)

Amazon's Product Advertising API requires an Associates account:

1. Sign up for [Amazon Associates](https://affiliate-program.amazon.com/)
2. Get API credentials from Associates Central
3. Set the environment variables:

```bash
export AMAZON_ACCESS_KEY="your_access_key"
export AMAZON_SECRET_KEY="your_secret_key"
export AMAZON_PARTNER_TAG="your_tag-20"
```

**Note:** The PA-API integration is marked for future implementation. Currently,
even with keys set, the adapter uses seed data. Contributions welcome!

## Using a .env file

Create a `.env` file in the repo root (it's git-ignored):

```
BESTBUY_API_KEY=your_key_here
WALMART_API_KEY=your_token_here
AMAZON_ACCESS_KEY=your_access_key
AMAZON_SECRET_KEY=your_secret_key
AMAZON_PARTNER_TAG=your_tag-20
```

Then load it before running:

```bash
source .env
python -m scripts.run_pipeline --zip 11201 --out xlsx
```

## Verify API mode

Run with verbose logging to confirm which mode each adapter uses:

```bash
python -m scripts.run_pipeline --zip 11201 -v
```

Look for lines like:
```
[BestBuy] API mode — querying products API
[Walmart] API mode — querying search API
[Amazon] BYO mode — returning 16 seed products
```
