#!/usr/bin/env python3
"""
Populate Notion Regions DB with canonical Geonode/ISO country list.

1. Backs up current Regions DB (Region Code, Region Name, Aliases) to JSON.
2. Archives all existing pages in the Regions DB.
3. Creates new pages for each canonical region (ISO 3166-1 alpha-2 + display name).

Usage:
  python scripts/populate_regions_db.py

Requires: NOTION_TOKEN, NOTION_REGIONS_DB_ID in .env
"""

import json
import os
import sys
import argparse
from pathlib import Path

# Load .env from project root
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

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_PATH = PROJECT_ROOT / "scrapers" / "data" / "regions_backup_adobe.json"

# Canonical list: ISO 3166-1 alpha-2 code -> display name (Geonode-compatible)
CANONICAL_REGIONS = [
    ("US", "United States"),
    ("GB", "United Kingdom"),
    ("DE", "Germany"),
    ("FR", "France"),
    ("CA", "Canada"),
    ("AU", "Australia"),
    ("IN", "India"),
    ("BR", "Brazil"),
    ("JP", "Japan"),
    ("MX", "Mexico"),
    ("AR", "Argentina"),
    ("TR", "Turkey"),
    ("PL", "Poland"),
    ("ZA", "South Africa"),
    ("NG", "Nigeria"),
    ("PH", "Philippines"),
    ("ID", "Indonesia"),
    ("TH", "Thailand"),
    ("VN", "Vietnam"),
    ("KR", "South Korea"),
    ("IT", "Italy"),
    ("ES", "Spain"),
    ("NL", "Netherlands"),
    ("BE", "Belgium"),
    ("SE", "Sweden"),
    ("NO", "Norway"),
    ("DK", "Denmark"),
    ("FI", "Finland"),
    ("IS", "Iceland"),
    ("AT", "Austria"),
    ("CH", "Switzerland"),
    ("CY", "Cyprus"),
    ("MT", "Malta"),
    ("BA", "Bosnia and Herzegovina"),
    ("MK", "North Macedonia"),
    ("AL", "Albania"),
    ("MD", "Moldova"),
    ("ME", "Montenegro"),
    ("PT", "Portugal"),
    ("IE", "Ireland"),
    ("LU", "Luxembourg"),
    ("NZ", "New Zealand"),
    ("SG", "Singapore"),
    ("MY", "Malaysia"),
    ("HK", "Hong Kong"),
    ("TW", "Taiwan"),
    ("CN", "China"),
    ("RU", "Russia"),
    ("UA", "Ukraine"),
    ("RO", "Romania"),
    ("CZ", "Czech Republic"),
    ("HU", "Hungary"),
    ("GR", "Greece"),
    ("IL", "Israel"),
    ("AE", "United Arab Emirates"),
    ("SA", "Saudi Arabia"),
    ("EG", "Egypt"),
    ("PK", "Pakistan"),
    ("BD", "Bangladesh"),
    ("CO", "Colombia"),
    ("CL", "Chile"),
    ("PE", "Peru"),
    ("EC", "Ecuador"),
    ("PR", "Puerto Rico"),
    ("CR", "Costa Rica"),
    ("GT", "Guatemala"),
    ("PA", "Panama"),
    ("CU", "Cuba"),
    ("DO", "Dominican Republic"),
    ("JM", "Jamaica"),
    ("VE", "Venezuela"),
    ("BO", "Bolivia"),
    ("PY", "Paraguay"),
    ("UY", "Uruguay"),
    ("SK", "Slovakia"),
    ("SI", "Slovenia"),
    ("HR", "Croatia"),
    ("BG", "Bulgaria"),
    ("LT", "Lithuania"),
    ("LV", "Latvia"),
    ("EE", "Estonia"),
    ("RS", "Serbia"),
    ("KE", "Kenya"),
    ("GH", "Ghana"),
    ("ET", "Ethiopia"),
    ("QA", "Qatar"),
    ("KW", "Kuwait"),
    ("OM", "Oman"),
    ("BH", "Bahrain"),
    ("JO", "Jordan"),
    ("LB", "Lebanon"),
    ("MA", "Morocco"),
    ("TZ", "Tanzania"),
    ("UG", "Uganda"),
    ("MM", "Myanmar"),
    ("LK", "Sri Lanka"),
    ("NP", "Nepal"),
    ("KZ", "Kazakhstan"),
    ("UZ", "Uzbekistan"),
    ("GE", "Georgia"),
    ("AZ", "Azerbaijan"),
    ("AM", "Armenia"),
    ("AF", "Afghanistan"),
    ("IQ", "Iraq"),
    ("IR", "Iran"),
    ("LY", "Libya"),
    ("TN", "Tunisia"),
    ("DZ", "Algeria"),
    ("SD", "Sudan"),
    ("SN", "Senegal"),
    ("CI", "Côte d'Ivoire"),
    ("CM", "Cameroon"),
    ("RW", "Rwanda"),
    ("BY", "Belarus"),
    ("TM", "Turkmenistan"),
    ("TJ", "Tajikistan"),
    ("KG", "Kyrgyzstan"),
    ("MN", "Mongolia"),
    ("LA", "Laos"),
    ("KH", "Cambodia"),
    ("MV", "Maldives"),
    # Aggregate / regional (for Adobe-style multi-country regions)
    ("CIS", "Commonwealth of Independent States"),
    ("MENA", "Middle East and North Africa"),
    ("XF", "Africa (regional)"),
    ("XL", "Latin America (regional)"),
]


def get_client() -> "Client":
    if Client is None:
        raise ValueError("notion-client is not installed. Run: pip install notion-client")
    token = os.getenv("NOTION_TOKEN")
    if not token or not token.strip():
        raise ValueError("NOTION_TOKEN is not set in .env")
    return Client(auth=token.strip())


def get_regions_db_id() -> str:
    db_id = os.getenv("NOTION_REGIONS_DB_ID")
    if not db_id or not db_id.strip():
        raise ValueError(
            "NOTION_REGIONS_DB_ID is not set in .env. "
            "Use the Regions database ID from its Notion URL."
        )
    return db_id.strip().replace("-", "")


def get_data_source_id(client: "Client", db_id: str) -> str:
    """Get the first data source ID from the Regions database (required for query in Notion API 2025+)."""
    db = client.databases.retrieve(database_id=db_id)
    data_sources = db.get("data_sources", [])
    if not data_sources:
        raise ValueError(f"Regions database {db_id} has no data sources.")
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


def backup_regions(client: "Client", data_source_id: str) -> list[dict]:
    """Fetch all pages from Regions DB and save to JSON. Returns list of backup records."""
    backup = []
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
            # Property names: Region Code (title), Region Name (rich_text), Aliases
            code = _extract_title(props, "Region Code")
            name = _extract_rich_text(props, "Region Name")
            aliases = _extract_rich_text(props, "Aliases")
            backup.append({
                "region_code": code,
                "region_name": name,
                "aliases": aliases,
                "page_id": page.get("id"),
            })
        has_more = resp.get("has_more", False)
        start_cursor = resp.get("next_cursor")

    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKUP_PATH, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2, ensure_ascii=False)
    return backup


def archive_all_pages(client: "Client", data_source_id: str) -> int:
    """Archive (soft-delete) all pages in the Regions DB. Returns count archived."""
    count = 0
    has_more = True
    start_cursor = None

    while has_more:
        resp = client.data_sources.query(
            data_source_id=data_source_id,
            start_cursor=start_cursor,
            page_size=100,
        )
        for page in resp.get("results", []):
            page_id = page.get("id")
            try:
                client.blocks.delete(block_id=page_id)
                count += 1
            except APIResponseError as e:
                print(f"  Warning: could not archive {page_id}: {e}")
        has_more = resp.get("has_more", False)
        start_cursor = resp.get("next_cursor")

    return count


def create_region_page(client: "Client", db_id: str, code: str, name: str) -> None:
    """Create one region page in the Regions DB."""
    client.pages.create(
        parent={"database_id": db_id},
        properties={
            "Region Code": {"title": [{"text": {"content": code}}]},
            "Region Name": {"rich_text": [{"text": {"content": name}}]},
        },
    )


def fetch_existing_regions(client: "Client", data_source_id: str) -> dict[str, dict]:
    """Return mapping Region Code -> page object (id + properties) for current Regions DB."""
    existing: dict[str, dict] = {}
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
            code = _extract_title(props, "Region Code").strip().upper()
            if code:
                existing[code] = page
        has_more = resp.get("has_more", False)
        start_cursor = resp.get("next_cursor")
    return existing


def update_region_name(client: "Client", page_id: str, name: str) -> None:
    """Update Region Name rich_text for an existing region page."""
    client.pages.update(
        page_id=page_id,
        properties={
            "Region Name": {"rich_text": [{"text": {"content": name}}]},
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Populate Notion Regions DB with canonical region list.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Archive all existing pages and recreate the full canonical list (DESTRUCTIVE to relations).",
    )
    parser.add_argument(
        "--update-names",
        action="store_true",
        help="When not resetting, update Region Name for existing codes to match the canonical display name.",
    )
    args = parser.parse_args()

    print("Regions DB: backup + clear + populate with canonical list")
    print("=" * 60)

    client = get_client()
    db_id = get_regions_db_id()
    data_source_id = get_data_source_id(client, db_id)

    # 1. Backup
    print("\n1. Backing up current Regions DB...")
    backup = backup_regions(client, data_source_id)
    print(f"   Backed up {len(backup)} rows to {BACKUP_PATH}")

    if args.reset:
        # 2. Archive all existing pages (DESTRUCTIVE: breaks relations)
        print("\n2. Archiving all existing pages in Regions DB (RESET MODE)...")
        archived = archive_all_pages(client, data_source_id)
        print(f"   Archived {archived} pages")

        # 3. Populate with canonical list (use database_id for creating pages)
        print(f"\n3. Creating {len(CANONICAL_REGIONS)} canonical region pages...")
        for code, name in CANONICAL_REGIONS:
            try:
                create_region_page(client, db_id, code, name)
                print(f"   + {code}: {name}")
            except APIResponseError as e:
                print(f"   Error creating {code}: {e}")
                return 1
    else:
        # Non-destructive mode: add missing regions only (safe for existing relations)
        print("\n2. Checking existing regions (non-destructive mode)...")
        existing = fetch_existing_regions(client, data_source_id)
        print(f"   Found {len(existing)} existing region pages")

        created = 0
        updated = 0
        print(f"\n3. Ensuring {len(CANONICAL_REGIONS)} canonical regions exist...")
        for code, name in CANONICAL_REGIONS:
            code_u = code.strip().upper()
            page = existing.get(code_u)
            if not page:
                try:
                    create_region_page(client, db_id, code_u, name)
                    created += 1
                    print(f"   + created {code_u}: {name}")
                except APIResponseError as e:
                    print(f"   Error creating {code_u}: {e}")
                    return 1
            elif args.update_names:
                # Update Region Name if different
                current_name = _extract_rich_text(page.get("properties", {}), "Region Name").strip()
                if current_name != name:
                    try:
                        update_region_name(client, page["id"], name)
                        updated += 1
                        print(f"   ~ updated {code_u}: {current_name} -> {name}")
                    except APIResponseError as e:
                        print(f"   Warning: could not update {code_u}: {e}")

        print(f"\n   Done. Created: {created}, Updated names: {updated}")

    print("\n" + "=" * 60)
    print("Done.")
    print(f"  Backup saved to: {BACKUP_PATH}")
    print("  Use regions_backup_adobe.json for Adobe region mapping later.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
