# Populate Regions DB

Populates the Notion **Regions** database with a canonical list of Geonode/ISO country codes and display names.

## What it does

1. **Backs up** the current Regions DB to `scrapers/data/regions_backup_adobe.json` (Region Code, Region Name, Aliases). Keep this file for Adobe region mapping later.
2. **Archives** all existing pages in the Regions DB (they go to Trash in Notion).
3. **Creates** one new page per canonical region (ISO 3166-1 alpha-2 code + display name). Ignores `href`; leaves Aliases empty.

## Setup

1. Add to `.env`:
   ```
   NOTION_REGIONS_DB_ID=28f31012cf48808baab5d6191f552f93
   ```
   (Use your Regions database ID from its Notion URL if different.)

2. Ensure `NOTION_TOKEN` is set (same as for other scrapers).

## Run

From the project root:

```bash
python scripts/populate_regions_db.py
```

## After running

- **Backup**: `scrapers/data/regions_backup_adobe.json` contains all previous Adobe region codes and names. Use this when mapping Adobe scraped data to the new Regions DB (e.g. "Pilipinas" → PH, "Deutschland" → DE).
- **Regions DB**: Now has 140+ canonical rows: ISO countries (US, GB, LU, PR, CY, MT, IS, …) plus aggregate regions (CIS, MENA, XF Africa, XL Latin America). Use these for Scraped Pricing relation and for Geonode-based scrapers.
- **Next**: Migrate Scraped Pricing to use Region as a relation to Regions DB and bulk-update existing Adobe rows using the backup mapping.
