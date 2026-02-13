# ChatGPT Plus Multi-Region Scraper

Scrapes ChatGPT Plus pricing across all regions in your Notion Regions DB using **patchright** (stealth browser automation) to bypass Cloudflare protection.

## Features

- **Cloudflare Bypass**: Uses patchright (patched Playwright) to bypass Cloudflare Turnstile
- **Geo-targeting**: Uses Geonode residential proxies for region-specific pricing
- **Dynamic Regions**: Fetches regions from your Notion Regions DB (125+ regions)
- **Auto-detection**: Handles multiple currencies (USD, EUR, GBP, INR, BRL, JPY, etc.)
- **Notion Integration**: Pushes results directly to Scraped Pricing DB

## Setup

### 1. Install Dependencies

```bash
pip install patchright
patchright install chromium
```

### 2. Sign up for Geonode (for geo-targeting)

1. Go to https://geonode.com
2. Sign up for the **$5 trial** (10GB for 3 days)
3. Get your credentials from the dashboard

### 3. Add Credentials to .env

```bash
# Required
NOTION_TOKEN=your-notion-token
NOTION_SCRAPED_PRICING_DB_ID=your-db-id
NOTION_REGIONS_DB_ID=your-regions-db-id

# Required for geo-targeting (--proxy flag)
GEONODE_USERNAME=your-username
GEONODE_PASSWORD=your-password
```

## Usage

### Scrape All Regions (with geo-targeting)

```bash
python -m scrapers.chatgpt_scraper --proxy --visible
```

This will:
1. Fetch all regions from your Notion Regions DB
2. For each region, open a browser window with Geonode proxy
3. Bypass Cloudflare and extract pricing
4. Push results to Scraped Pricing DB

**Estimated time**: ~30-60 minutes for 125 regions

### Scrape Single Region

```bash
python -m scrapers.chatgpt_scraper --country US --proxy --visible
python -m scrapers.chatgpt_scraper --country IN --proxy --visible
python -m scrapers.chatgpt_scraper --country BR --proxy --visible
```

### Scrape Without Proxy (uses your IP's location)

```bash
python -m scrapers.chatgpt_scraper --country US
```

### Debug Mode (saves HTML for inspection)

```bash
python -m scrapers.chatgpt_scraper --country US --proxy --visible --debug
```

## Command Line Options

| Flag | Description |
|------|-------------|
| `--country XX` | Scrape only a specific country code (e.g., US, GB, IN) |
| `--proxy` | Use Geonode proxy for geo-targeting |
| `--visible` | Run browser visibly (required with --proxy for Cloudflare bypass) |
| `--debug` | Save fetched HTML to `scrapers/data/debug_XX.html` |
| `--patchright` | Use patchright mode (default) |
| `--direct` | Use direct Playwright + proxy (may be blocked) |

## How It Works

1. **Fetches regions** from Notion Regions DB
2. **For each region**:
   - Launches Chrome via patchright (stealth mode)
   - Connects through Geonode proxy for geo-targeting
   - Navigates to https://chatgpt.com/pricing
   - Waits for Cloudflare challenge to pass (auto-clicks checkbox if needed)
   - Waits for React to render pricing (event-driven, not polling)
   - Extracts price, currency, and period
   - Pushes to Notion Scraped Pricing DB
3. **Rate limiting**: 2-second delay between regions

## Supported Currencies

The scraper automatically detects and parses:
- USD ($), EUR (€), GBP (£), INR (₹), JPY (¥)
- BRL (R$), ZAR, MXN, ARS, TRY, PLN
- PHP, IDR, THB, NGN, and more

## Cost

**Geonode usage**: ~50MB per full scrape (125 regions)
- At $3/GB = ~$0.15 per full scrape
- The $5 trial (10GB) = ~200 full scrapes

## Scheduling

### Option A: Manual

Run when needed:
```bash
cd /Users/tyler/Desktop/priceduck
source venv/bin/activate
python -m scrapers.chatgpt_scraper --proxy --visible
```

### Option B: Cron (runs weekly)

```bash
crontab -e
```

Add (runs every Sunday at 2am):
```
0 2 * * 0 cd /Users/tyler/Desktop/priceduck && ./venv/bin/python -m scrapers.chatgpt_scraper --proxy --visible >> /tmp/chatgpt_scraper.log 2>&1
```

**Note**: Cron runs without a display, so `--visible` may not work. For automated runs, you may need to use a headless approach or run on a machine with a display.

## Troubleshooting

### "Missing Geonode credentials"
→ Add `GEONODE_USERNAME` and `GEONODE_PASSWORD` to `.env`

### "Could not fetch regions from Notion"
→ Check `NOTION_REGIONS_DB_ID` in `.env` and ensure the Regions DB is shared with your integration

### "Cloudflare challenge did not pass"
→ The Turnstile challenge wasn't solved. Try running again - it's intermittent. Using `--visible` mode helps.

### "Warning: prices may not have fully rendered"
→ React hydration was slow. The scraper waits up to 60 seconds. If this happens consistently for a region, the proxy connection may be slow.

### "Failed to parse price"
→ Check if ChatGPT changed their page structure. Run with `--debug` and inspect the HTML.

### Browser window stays open
→ An error occurred. The script should close the browser automatically, but if not, close it manually.

## Example Output

```
ChatGPT Plus Multi-Region Scraper
=================================
Target: https://chatgpt.com/pricing
Mode: patchright (FREE, stealth Playwright - best option)
Fetching regions from Notion...
Found 125 regions in Notion Regions DB
Regions to scrape: 125

[US] Scraping United States...
  [US] Fetching via patchright (visible + proxy)...
  [US] Found pricing section
  [US] Price rendered: $20 / month
  [US] Found: 20.0 USD / Monthly (Plus)
  [US] ✓ Pushed to Scraped Pricing DB

[GB] Scraping United Kingdom...
  [GB] Fetching via patchright (visible + proxy)...
  [GB] Found pricing section
  [GB] Price rendered: £20 / month
  [GB] Found: 20.0 GBP / Monthly (Plus)
  [GB] ✓ Pushed to Scraped Pricing DB

...

==================================================
Done! Success: 123, Failed: 2
==================================================
```

## Architecture

```
chatgpt_scraper.py
    ├── Uses patchright for Cloudflare bypass
    ├── Uses Geonode proxy for geo-targeting
    ├── Fetches regions from regions.py → Notion Regions DB
    ├── Extracts prices with BeautifulSoup
    └── Pushes to notion_client.py → Notion Scraped Pricing DB
```
