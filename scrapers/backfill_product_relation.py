"""
Backfill script: populate 'Product Relation' on all Scraped Pricing rows
based on the existing 'Product' select value.

Usage:
    cd /path/to/priceduck
    python scrapers/backfill_product_relation.py [--dry-run]

Requires: NOTION_TOKEN, NOTION_SCRAPED_PRICING_DB_ID in .env
"""

import os
import sys
import time
import json
import argparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # env vars must be set manually

import requests

# ── Config ───────────────────────────────────────────────────────────────
NOTION_VERSION = "2022-06-28"
BASE = "https://api.notion.com/v1"

# Product name (select value) → Products DB page ID
PRODUCT_MAP = {
    "Creative Cloud All Apps": "c7993fc0-b385-428a-bc35-9fe5d938f60e",
    "ChatGPT Plus": "2fa31012-cf48-803a-8e07-ea357d9a0997",
}


def headers():
    token = os.getenv("NOTION_TOKEN")
    if not token:
        sys.exit("NOTION_TOKEN is not set")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def fetch_all_pages(db_id: str) -> list[dict]:
    """Paginate through all rows in the Scraped Pricing DB."""
    pages = []
    payload: dict = {"page_size": 100}
    while True:
        resp = requests.post(f"{BASE}/databases/{db_id}/query", headers=headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()
        pages.extend(data["results"])
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
        print(f"  fetched {len(pages)} rows so far…", flush=True)
    return pages


def update_page(page_id: str, product_page_id: str):
    payload = {
        "properties": {
            "Product Relation": {
                "relation": [{"id": product_page_id}]
            }
        }
    }
    resp = requests.patch(f"{BASE}/pages/{page_id}", headers=headers(), json=payload)
    resp.raise_for_status()


def run(dry_run: bool = False):
    db_id = os.getenv("NOTION_SCRAPED_PRICING_DB_ID")
    if not db_id:
        sys.exit("NOTION_SCRAPED_PRICING_DB_ID is not set")

    print(f"Fetching all Scraped Pricing rows from {db_id}…", flush=True)
    pages = fetch_all_pages(db_id)
    print(f"Total rows: {len(pages)}", flush=True)

    updated = 0
    skipped_already_set = 0
    skipped_no_product = 0
    skipped_unknown = 0
    errors = 0

    for i, page in enumerate(pages):
        page_id = page["id"]
        props = page["properties"]

        # Check if Product Relation is already set
        product_rel = props.get("Product Relation", {})
        existing_relations = product_rel.get("relation", [])
        if existing_relations:
            skipped_already_set += 1
            continue

        # Get Product select value
        product_prop = props.get("Product", {})
        product_select = product_prop.get("select")
        if not product_select:
            skipped_no_product += 1
            continue

        product_name = product_select.get("name", "")
        target_page_id = PRODUCT_MAP.get(product_name)
        if not target_page_id:
            skipped_unknown += 1
            if skipped_unknown <= 5:
                print(f"  WARNING: Unknown product '{product_name}' on page {page_id}")
            continue

        if dry_run:
            updated += 1
            continue

        # Update the row
        try:
            update_page(page_id, target_page_id)
            updated += 1
            # Rate limit: Notion API allows ~3 requests/sec
            if updated % 3 == 0:
                time.sleep(1.1)
        except Exception as e:
            errors += 1
            print(f"  ERROR updating {page_id}: {e}")

        if (i + 1) % 50 == 0:
            print(f"  processed {i + 1}/{len(pages)} ({updated} updated)", flush=True)

    action = "would update" if dry_run else "updated"
    print(f"\nDone! {action} {updated} rows")
    print(f"  already set: {skipped_already_set}")
    print(f"  no product:  {skipped_no_product}")
    print(f"  unknown:     {skipped_unknown}")
    print(f"  errors:      {errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill Product Relation on Scraped Pricing rows")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without updating Notion")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
