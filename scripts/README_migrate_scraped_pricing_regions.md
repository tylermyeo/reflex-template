# Migrate Scraped Pricing: Region Name → Region (Relation)

This script migrates the **Scraped Pricing** database from an old region column (Select or Rich Text with Adobe-style names) to a **Relation** to the **Regions** database. It preserves mapping from Adobe region codes and names to canonical ISO regions and can optionally fill the **Aliases** column in the Regions DB so those names are kept for audit and URL-param reference.

## Prerequisites

1. **Regions DB** must already be populated with the canonical list (run `python scripts/populate_regions_db.py` first).

2. **In Notion – Scraped Pricing database:**
   - Add a new property: **Region Relation** (type: **Relation** → choose your **Regions** database, single relation).
   - Leave the existing **Region Name** (Select) column in place until after you’ve run the migration and verified results.

3. **`.env`** must include:
   - `NOTION_TOKEN`
   - `NOTION_SCRAPED_PRICING_DB_ID`
   - `NOTION_REGIONS_DB_ID`

4. **Backup file** (optional but recommended): `scrapers/data/regions_backup_adobe.json` from before you ran `populate_regions_db.py`. If present, the script uses it to map Adobe region codes and names to canonical Region Codes.

## What the script does

1. **Optional: populate Regions DB Aliases**  
   If you pass `--populate-aliases`, the script updates each row in the **Regions** DB so that the **Aliases** field lists all Adobe `region_code` and `region_name` values that map to that canonical region (e.g. for **SA** you get `sa_en, sa_ar, Saudi Arabia - English, المملكة العربية السعودية`).  
   - This keeps original Adobe names in one place.
   - **Products DB “Available Regions” and URL params** are unchanged; the scraper continues to use those values as-is for building URLs.

2. **Build mapping**  
   From the backup (and built-in overrides like `uk` → `GB`), it builds:  
   `Adobe value (code or name) → canonical Region Code (e.g. US, SA, GB)`.

3. **Migrate Scraped Pricing**  
   It loads all Scraped Pricing rows, reads the current region from the **old** property (`Region Name` or whatever you pass with `--old-property`), resolves it to a Regions DB page via the mapping, and sets the **new** Relation property (`Region` by default) to that page.

## Usage

From the project root:

```bash
# Dry run: show what would be done, no Notion updates
python scripts/migrate_scraped_pricing_regions.py --dry-run

# Populate Regions DB Aliases from backup, then migrate Scraped Pricing (dry run)
python scripts/migrate_scraped_pricing_regions.py --dry-run --populate-aliases

# Do it for real: fill Aliases, then set Region relation on all Scraped Pricing rows
python scripts/migrate_scraped_pricing_regions.py --populate-aliases

# Migrate only (Aliases already filled or not needed)
python scripts/migrate_scraped_pricing_regions.py
```

### Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Log actions only; do not update Notion. |
| `--populate-aliases` | First update Regions DB **Aliases** from `scrapers/data/regions_backup_adobe.json`. |
| `--old-property NAME` | Scraped Pricing property that currently holds the region (default: `Region Name`). |
| `--new-property NAME` | Scraped Pricing property for the relation to Regions DB (default: `Region Relation`). |
| `--delay SECS` | Seconds to wait between page updates to avoid rate limits (default: `0.35`). |

The script reads from **Region Name** (Select) and writes to **Region Relation** (Relation) by default. If you used different names:

```bash
python scripts/migrate_scraped_pricing_regions.py --old-property "Region Name" --new-property "Region Relation"
```

## After migration

1. In Notion, spot-check Scraped Pricing: **Region** should link to the correct Regions DB row.
2. If you no longer need the old column, remove it from the Scraped Pricing database in Notion.
3. **Products DB** and scraping scripts keep using **Available Regions** and **Region URL Pattern** as before; original Adobe codes/names used in URL params remain there and (if you used `--populate-aliases`) are also recorded in Regions DB **Aliases**.

## Unmapped values

If the script reports “Unmapped” for some rows:

- The old value wasn’t in the backup and isn’t a 2-letter canonical code, or  
- The canonical code (e.g. from first two letters of an Adobe code) doesn’t exist in the current Regions DB (e.g. aggregate regions like CIS, MENA).

You can add more overrides in the script’s `ADOBE_TO_CANONICAL_OVERRIDES` or add missing canonical regions to the Regions DB and re-run.
