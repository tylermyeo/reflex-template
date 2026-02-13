# PriceDuck Automated Pricing Scraper

Scrapes pricing data from SaaS websites and pushes it to a Notion database. Uses Gemini AI to discover CSS selectors for new products. Products and selectors are managed in the Notion **Products DB**.

## Prerequisites

- Python 3.9+
- Notion workspace with an integration connected to Products DB and Scraped Pricing DB
- Gemini API key (Google AI)

## Setup

### 1. Install Dependencies

From the project root:

```bash
pip install -r requirements.txt
```

For JavaScript-rendered pages, install Playwright browsers:

```bash
playwright install chromium
```

### 2. Notion Databases

You need two Notion databases:

#### Products DB (source of truth)

This is your existing Products database. The scraper added these properties:

| Property           | Type      | Description                         |
|--------------------|-----------|-------------------------------------|
| Product Name       | Title     | Name of the product                 |
| Product URL        | URL       | Pricing page URL to scrape          |
| Selector Price     | Rich Text | CSS selector for price amount       |
| Selector Currency  | Rich Text | CSS selector for currency           |
| Selector Period    | Rich Text | CSS selector for billing period     |
| Selector Plan Name | Rich Text | CSS selector for plan/tier name     |
| Rendering          | Select    | `static` (requests) or `js` (Playwright) |

The following existing properties are managed by other automations (do not touch):
- Min USD Price, Cheapest Region, Pages, Cheapest Page

#### Scraped Pricing DB (output)

Create a database named **"Scraped Pricing"** with:

| Property     | Type      | Description                    |
|--------------|-----------|--------------------------------|
| Product Name | Title     | Name of the product/plan       |
| Amount       | Number    | Numeric price value            |
| Currency     | Select    | USD, EUR, GBP, etc.            |
| Period       | Select    | Monthly, Yearly, One-time      |
| Plan Name    | Rich Text | Tier name if applicable        |
| Scraped At   | Date      | Timestamp of scrape            |
| Success      | Checkbox  | Whether scrape succeeded       |
| Source URL   | URL       | Link to pricing page           |
| Notes        | Rich Text | Error messages or extra info   |

Connect your integration to both databases:
1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create an integration and copy the secret token
3. In each database, click "..." → "Connections" → add your integration

### 3. Environment Variables

Copy `.env.example` to `.env` and fill in:

```
NOTION_TOKEN=secret_xxx
NOTION_PRODUCTS_DB_ID=0809cffb842e44a5a69f96f7b653de33
NOTION_SCRAPED_PRICING_DB_ID=your-scraped-pricing-db-id
GEMINI_API_KEY=your-gemini-api-key
```

- **NOTION_TOKEN**: From notion.so/my-integrations
- **NOTION_PRODUCTS_DB_ID**: Your Products database ID (already set to default)
- **NOTION_SCRAPED_PRICING_DB_ID**: The Scraped Pricing database ID
- **GEMINI_API_KEY**: From [ai.google.dev](https://ai.google.dev) or [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Workflow

### Adding a New Product

1. In Notion Products DB, add a row with:
   - **Product Name**: e.g., "ChatGPT Plus"
   - **Product URL**: e.g., "https://openai.com/chatgpt/pricing"

2. Run selector discovery:
   ```bash
   python -m scrapers.selector_discovery
   ```
   This finds all products without selectors and uses Gemini to discover them, then saves them back to Notion.

3. Run the scraper:
   ```bash
   python -m scrapers.main_scraper
   ```
   This scrapes all products that have selectors and pushes results to Scraped Pricing.

### Discovering Selectors

**For all products needing selectors:**

```bash
python -m scrapers.selector_discovery
```

**For a single URL (lookup or one-off):**

```bash
python -m scrapers.selector_discovery --url https://example.com/pricing
```

If the URL matches a product in Notion, selectors are saved. Otherwise, it prints instructions for adding the product.

**Options:**

- `--js` — Use Playwright for JS-rendered pages
- `--no-test` — Skip testing selectors against the page
- `--name "Product Name"` — Override product name in output

### Running the Scraper

```bash
python -m scrapers.main_scraper
```

The scraper:

- Loads products from Notion Products DB (only those with selectors)
- Fetches each pricing page (requests or Playwright based on Rendering field)
- Extracts data using stored selectors
- Pushes results to Scraped Pricing DB
- Waits 2 seconds between products (rate limiting)
- Logs to console and `scrapers/logs/`

## Troubleshooting

### "NOTION_TOKEN environment variable is not set"

Ensure `.env` exists in the project root and contains `NOTION_TOKEN`.

### "NOTION_PRODUCTS_DB_ID environment variable is not set"

Add `NOTION_PRODUCTS_DB_ID=0809cffb842e44a5a69f96f7b653de33` to your `.env` file.

### "Notion API error: Could not find database"

- Verify the database ID is correct (32-character UUID)
- Ensure your integration is connected to the database (database → ... → Connections)

### "GEMINI_API_KEY environment variable is not set"

Get a key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and add it to `.env`.

### "No products need discovery"

All products in the Products DB either:
- Already have selectors (Selector Price is set), or
- Don't have a Product URL set

Add a Product URL to products you want to scrape.

### Selectors return "(not found)"

- The page structure may have changed — run selector discovery again
- For JS-rendered content, set Rendering to `js` in Notion, or use `--js` flag

### Price parsing fails

The scraper handles formats like `$19.99`, `19,99 €`, `USD 19.99`. If extraction fails, the selector may be capturing extra text. Use a more specific selector.

### Playwright "Executable doesn't exist"

Run:

```bash
playwright install chromium
```

## Automation (Optional)

To run weekly (e.g., Sunday 12:00 PM), add a cron job:

```bash
0 12 * * 0 cd /path/to/priceduck && python -m scrapers.main_scraper
```

Or use macOS LaunchAgent, Railway cron, or GitHub Actions for scheduled runs.

## File Structure

```
scrapers/
├── __init__.py
├── selector_discovery.py   # Discovers selectors using Gemini, saves to Notion
├── main_scraper.py         # Scrapes products from Notion, pushes to Scraped Pricing
├── notion_client.py        # Scraped Pricing DB client (push results)
├── products_client.py      # Products DB client (load products, update selectors)
├── README.md               # This file
└── logs/                   # Scraper run logs
```
