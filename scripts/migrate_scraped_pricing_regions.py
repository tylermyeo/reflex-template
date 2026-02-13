#!/usr/bin/env python3
"""
Migrate Scraped Pricing DB: old Region Name (Select/Text) → Region (Relation to Regions DB).

1. Optionally populate Regions DB Aliases from regions_backup_adobe.json so each
   canonical row lists Adobe region_code and region_name (for mapping and audit).
2. Build mapping: Adobe value → canonical Region Code (from backup + overrides).
3. Query Scraped Pricing rows, resolve each old region value to a Regions DB page id,
   and set the Region relation.

Prerequisites:
- In Notion: Add a new property "Region Relation" (Relation → Regions DB, single) to the
  Scraped Pricing database. Leave the old "Region Name" (Select) in place until after
  migration and verification.
- Regions DB must already be populated with canonical list (run populate_regions_db.py first).
- .env: NOTION_TOKEN, NOTION_SCRAPED_PRICING_DB_ID, NOTION_REGIONS_DB_ID.

Usage:
  python scripts/migrate_scraped_pricing_regions.py [--dry-run] [--populate-aliases] [--old-property NAME] [--new-property NAME]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError
except ImportError:
    Client = None
    APIResponseError = Exception  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_PATH = PROJECT_ROOT / "scrapers" / "data" / "regions_backup_adobe.json"

# Adobe region_code that don't map by first-2-chars (e.g. UK → GB) or aggregate → canonical
ADOBE_TO_CANONICAL_OVERRIDES: dict[str, str] = {
    "uk": "GB",
    "africa": "XF",  # Africa (regional) – avoid mapping to AF (Afghanistan)
    "la": "XL",      # Latin America (regional) – avoid mapping to LA (Laos)
    "cis_en": "CIS",
    "cis_ru": "CIS",
    "mena_ar": "MENA",
    "mena_en": "MENA",
}

# No longer excluding any; aggregates map to CIS, MENA, XF, XL in Regions DB
ADOBE_NO_CANONICAL: frozenset[str] = frozenset()


def get_client() -> "Client":
    if Client is None:
        raise ValueError("notion-client is not installed. Run: pip install notion-client")
    token = os.getenv("NOTION_TOKEN")
    if not token or not token.strip():
        raise ValueError("NOTION_TOKEN is not set in .env")
    return Client(auth=token.strip())


def get_scraped_pricing_db_id() -> str:
    db_id = os.getenv("NOTION_SCRAPED_PRICING_DB_ID")
    if not db_id or not db_id.strip():
        raise ValueError("NOTION_SCRAPED_PRICING_DB_ID is not set in .env")
    return db_id.strip().replace("-", "")


def get_regions_db_id() -> str:
    db_id = os.getenv("NOTION_REGIONS_DB_ID")
    if not db_id or not db_id.strip():
        raise ValueError("NOTION_REGIONS_DB_ID is not set in .env")
    return db_id.strip().replace("-", "")


def get_data_source_id(client: "Client", db_id: str) -> str:
    db = client.databases.retrieve(database_id=db_id)
    data_sources = db.get("data_sources", [])
    if not data_sources:
        raise ValueError(f"Database {db_id} has no data sources.")
    return data_sources[0]["id"]


def _extract_title(props: dict, name: str) -> str:
    prop = props.get(name, {})
    if prop.get("type") == "title":
        return "".join(t.get("plain_text", "") for t in prop.get("title", []))
    return ""


def _extract_rich_text(props: dict, name: str) -> str:
    prop = props.get(name, {})
    if prop.get("type") == "rich_text":
        return "".join(t.get("plain_text", "") for t in prop.get("rich_text", []))
    return ""


def _extract_select(props: dict, name: str) -> str:
    prop = props.get(name, {})
    if prop.get("type") == "select":
        sel = prop.get("select")
        if sel:
            return (sel.get("name") or "").strip()
    return ""


def extract_region_value(props: dict, old_property: str) -> str:
    """Get the current region string from a page (Select or Rich Text)."""
    prop = props.get(old_property, {})
    t = prop.get("type", "")
    if t == "select":
        return _extract_select(props, old_property)
    if t == "rich_text":
        return _extract_rich_text(props, old_property)
    return ""


# ---------------------------------------------------------------------------
# 1. Load backup and build Adobe value → canonical code
# ---------------------------------------------------------------------------


def load_backup() -> list[dict]:
    if not BACKUP_PATH.exists():
        return []
    with open(BACKUP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_adobe_to_canonical(backup: list[dict]) -> dict[str, str]:
    """Map every Adobe region_code and region_name to canonical ISO code (e.g. US, SA)."""
    out: dict[str, str] = {}
    for row in backup:
        code = (row.get("region_code") or "").strip().lower()
        name = (row.get("region_name") or "").strip()
        aliases = (row.get("aliases") or "").strip()
        if not code:
            continue
        if code in ADOBE_NO_CANONICAL:
            continue
        canonical = ADOBE_TO_CANONICAL_OVERRIDES.get(code)
        if canonical is None:
            canonical = code[:2].upper()
        # Also support the case where regions_backup_adobe.json has already been overwritten
        # by a later run of populate_regions_db.py. In that case, backup rows are canonical
        # Region Code/Name, and the Adobe names/codes live in the Aliases field.
        alias_vals: list[str] = []
        if aliases:
            # Aliases are stored as comma-separated values (may include non-Latin scripts).
            alias_vals = [a.strip() for a in aliases.split(",") if a and a.strip()]

        for val in (code, code.upper(), name, *alias_vals):
            if val:
                out[val] = canonical
                out[val.lower()] = canonical
    return out


# ---------------------------------------------------------------------------
# 2. Optionally populate Regions DB Aliases from backup
# ---------------------------------------------------------------------------


def populate_regions_aliases(client: "Client", regions_db_id: str, backup: list[dict], dry_run: bool) -> None:
    """For each canonical region in Regions DB, set Aliases to Adobe codes/names that map to it."""
    data_source_id = get_data_source_id(client, regions_db_id)
    # Collect canonical_code -> set of alias strings (codes, names, and any backup aliases)
    by_canonical: dict[str, set[str]] = {}
    for row in backup:
        code = (row.get("region_code") or "").strip().lower()
        name = (row.get("region_name") or "").strip()
        aliases = (row.get("aliases") or "").strip()
        if not code or code in ADOBE_NO_CANONICAL:
            continue
        canonical = ADOBE_TO_CANONICAL_OVERRIDES.get(code) or code[:2].upper()
        s = by_canonical.setdefault(canonical, set())
        if code:
            s.add(code)
            s.add(code.upper())
        if name:
            s.add(name)
        if aliases:
            for a in aliases.split(","):
                a = a.strip()
                if a:
                    s.add(a)

    # Fetch current Regions DB pages to get page_id by Region Code
    code_to_page: dict[str, tuple[str, set[str]]] = {}
    has_more = True
    start_cursor = None
    while has_more:
        resp = client.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=start_cursor,
            page_size=100,
        )
        for page in resp.get("results", []):
            props = page.get("properties", {})
            rc = _extract_title(props, "Region Code").strip().upper()
            if rc:
                code_to_page[rc] = (page["id"], by_canonical.get(rc, set()))
        has_more = resp.get("has_more", False)
        start_cursor = resp.get("next_cursor")

    for canonical, (page_id, alias_set) in code_to_page.items():
        if not alias_set:
            continue
        # Stable-ish ordering for readability (case-insensitive)
        parts = sorted(alias_set, key=lambda x: x.lower())
        aliases_str = ", ".join(parts)
        if dry_run:
            print(f"  [dry-run] Would set Aliases for {canonical}: {aliases_str[:80]}...")
            continue
        try:
            client.pages.update(
                page_id=page_id,
                properties={"Aliases": {"rich_text": [{"text": {"content": aliases_str[:2000]}}]}},
            )
            print(f"  Set Aliases for {canonical} ({len(parts)} values)")
        except APIResponseError as e:
            print(f"  Warning: failed to update {canonical}: {e}")


# ---------------------------------------------------------------------------
# 3. Build canonical code → Regions DB page id
# ---------------------------------------------------------------------------


def fetch_regions_code_to_page_id(client: "Client", regions_db_id: str) -> dict[str, str]:
    """Return mapping canonical Region Code -> page_id."""
    data_source_id = get_data_source_id(client, regions_db_id)
    result: dict[str, str] = {}
    has_more = True
    start_cursor = None
    while has_more:
        resp = client.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=start_cursor,
            page_size=100,
        )
        for page in resp.get("results", []):
            code = _extract_title(page.get("properties", {}), "Region Code").strip().upper()
            if code:
                result[code] = page["id"]
        has_more = resp.get("has_more", False)
        start_cursor = resp.get("next_cursor")
    return result


# ---------------------------------------------------------------------------
# 4. Query Scraped Pricing and update each row
# ---------------------------------------------------------------------------


def migrate_scraped_pricing(
    client: "Client",
    scraped_db_id: str,
    adobe_to_canonical: dict[str, str],
    code_to_page_id: dict[str, str],
    old_property: str,
    new_property: str,
    dry_run: bool,
    delay: float,
) -> tuple[int, int, int]:
    """Update Scraped Pricing rows with Region relation. Returns (updated, skipped_no_value, unmapped)."""
    data_source_id = get_data_source_id(client, scraped_db_id)
    updated = 0
    skipped = 0
    unmapped = 0
    has_more = True
    start_cursor = None

    while has_more:
        resp = client.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=start_cursor,
            page_size=100,
        )
        for page in resp.get("results", []):
            page_id = page["id"]
            props = page.get("properties", {})
            old_value = extract_region_value(props, old_property).strip()
            if not old_value:
                skipped += 1
                continue
            # Resolve: old value (Adobe name/code) -> canonical code -> page_id
            canonical = adobe_to_canonical.get(old_value) or adobe_to_canonical.get(old_value.lower())
            if not canonical and len(old_value.strip()) == 2:
                canonical = old_value.strip().upper()
            if not canonical:
                unmapped += 1
                if unmapped <= 20:
                    print(f"  Unmapped: '{old_value}' (page {page_id[:8]}...)")
                continue
            region_page_id = code_to_page_id.get(canonical)
            if not region_page_id:
                unmapped += 1
                if unmapped <= 20:
                    print(f"  No Regions DB page for canonical '{canonical}' (old value '{old_value}')")
                continue
            if dry_run:
                print(f"  [dry-run] Would set {new_property} -> {canonical} for page {page_id[:8]}...")
                updated += 1
                continue
            try:
                client.pages.update(
                    page_id=page_id,
                    properties={new_property: {"relation": [{"id": region_page_id}]}},
                )
                updated += 1
                if updated % 100 == 0:
                    print(f"  Updated {updated} rows...")
            except APIResponseError as e:
                print(f"  Error updating page {page_id}: {e}")
            if delay > 0:
                time.sleep(delay)
        has_more = resp.get("has_more", False)
        start_cursor = resp.get("next_cursor")

    return updated, skipped, unmapped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate Scraped Pricing Region Name to Region (relation to Regions DB)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only print what would be done; do not update Notion.",
    )
    parser.add_argument(
        "--populate-aliases",
        action="store_true",
        help="First update Regions DB Aliases from regions_backup_adobe.json.",
    )
    parser.add_argument(
        "--old-property",
        default="Region Name",
        help="Scraped Pricing property name that currently holds the region (Select or Rich Text). Default: Region Name",
    )
    parser.add_argument(
        "--new-property",
        default="Region Relation",
        help="Scraped Pricing property name for the relation to Regions DB. Default: Region Relation",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.35,
        help="Seconds to wait between page updates (rate limit). Default: 0.35",
    )
    args = parser.parse_args()

    print("Migrate Scraped Pricing: Region Name → Region (relation)")
    print("=" * 60)
    if args.dry_run:
        print("DRY RUN – no changes will be made.")
        print()

    client = get_client()
    scraped_db_id = get_scraped_pricing_db_id()
    regions_db_id = get_regions_db_id()

    backup = load_backup()
    if not backup:
        print("Warning: No regions_backup_adobe.json found; only exact 2-letter codes will resolve.")
    else:
        print(f"Loaded {len(backup)} Adobe regions from backup.")

    adobe_to_canonical = build_adobe_to_canonical(backup)
    print(f"Built mapping for {len(adobe_to_canonical)} Adobe values -> canonical code.")

    if args.populate_aliases:
        print("\nPopulating Regions DB Aliases from backup...")
        populate_regions_aliases(client, regions_db_id, backup, args.dry_run)

    print("\nFetching Regions DB (canonical code -> page id)...")
    code_to_page_id = fetch_regions_code_to_page_id(client, regions_db_id)
    print(f"  {len(code_to_page_id)} canonical regions in Regions DB.")

    print(f"\nMigrating Scraped Pricing (old: '{args.old_property}' -> new: '{args.new_property}')...")
    updated, skipped, unmapped = migrate_scraped_pricing(
        client,
        scraped_db_id,
        adobe_to_canonical,
        code_to_page_id,
        args.old_property,
        args.new_property,
        args.dry_run,
        args.delay,
    )

    print()
    print("Summary:")
    print(f"  Updated (relation set): {updated}")
    print(f"  Skipped (no old value): {skipped}")
    print(f"  Unmapped (no canonical or not in Regions DB): {unmapped}")
    if args.dry_run:
        print()
        print("Run without --dry-run to apply changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
