"""
Regions helpers for scrapers.

Scrapers should write region using the Scraped Pricing DB relation property:
  "Region Relation" (Relation → Regions DB)

This module resolves a region *value* (canonical code like "US", or an Adobe-style
region code/name like "sa_en" / "Saudi Arabia - English") to the corresponding
Regions DB page id.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

# Load .env from project root
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

_CACHE_PATH = Path(__file__).resolve().parent / "data" / "regions_page_ids.json"

# Special-case overrides (avoid ambiguous first-2-chars heuristics)
_VALUE_TO_CANONICAL_OVERRIDES: dict[str, str] = {
    "uk": "GB",
    "africa": "XF",  # Africa (regional) – avoid AF (Afghanistan)
    "la": "XL",  # Latin America (regional) – avoid LA (Laos)
    "cis_en": "CIS",
    "cis_ru": "CIS",
    "mena_ar": "MENA",
    "mena_en": "MENA",
}


def _get_client():
    from scrapers.notion_client import get_notion_client

    return get_notion_client()


def _get_regions_db_id() -> Optional[str]:
    db_id = os.getenv("NOTION_REGIONS_DB_ID")
    if not db_id or not db_id.strip():
        return None
    return db_id.strip().replace("-", "")


def _get_data_source_id(client, db_id: str) -> Optional[str]:
    db = client.databases.retrieve(database_id=db_id)
    data_sources = db.get("data_sources", [])
    if not data_sources:
        return None
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


def _load_cache() -> dict:
    if not _CACHE_PATH.exists():
        return {}
    try:
        with open(_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(data: dict) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_regions_maps() -> tuple[dict[str, str], dict[str, str]]:
    """
    Fetch Regions DB once and return:
      - code_to_page_id: canonical Region Code -> page_id
      - alias_to_page_id: alias token (lowercased) -> page_id

    Aliases are read from the Regions DB "Aliases" rich_text property and split on commas.
    """
    db_id = _get_regions_db_id()
    if not db_id:
        return {}, {}

    client = _get_client()
    data_source_id = _get_data_source_id(client, db_id)
    if not data_source_id:
        return {}, {}

    code_to_page_id: dict[str, str] = {}
    alias_to_page_id: dict[str, str] = {}

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
            if not code:
                continue
            page_id = page.get("id")
            if not page_id:
                continue

            code_to_page_id[code] = page_id
            alias_to_page_id[code.lower()] = page_id

            aliases = _extract_rich_text(props, "Aliases").strip()
            if aliases:
                for token in aliases.split(","):
                    t = token.strip()
                    if t:
                        alias_to_page_id[t.lower()] = page_id

        has_more = resp.get("has_more", False)
        start_cursor = resp.get("next_cursor")

    return code_to_page_id, alias_to_page_id


def ensure_regions_cache(force_refresh: bool = False) -> tuple[dict[str, str], dict[str, str]]:
    """
    Return (code_to_page_id, alias_to_page_id) from cache if present; otherwise fetch and cache.
    Cache format:
      {"code_to_page_id": {...}, "alias_to_page_id": {...}}
    """
    if not force_refresh:
        cached = _load_cache()
        if (
            isinstance(cached.get("code_to_page_id"), dict)
            and isinstance(cached.get("alias_to_page_id"), dict)
            and cached["code_to_page_id"]
        ):
            return cached["code_to_page_id"], cached["alias_to_page_id"]

    code_to_page_id, alias_to_page_id = fetch_regions_maps()
    _save_cache({"code_to_page_id": code_to_page_id, "alias_to_page_id": alias_to_page_id})
    return code_to_page_id, alias_to_page_id


def fetch_all_regions() -> list[tuple[str, str]]:
    """
    Fetch all regions from the Notion Regions DB.
    
    Returns a list of (region_code, region_name) tuples.
    Example: [("US", "United States"), ("GB", "United Kingdom"), ...]
    """
    db_id = _get_regions_db_id()
    if not db_id:
        return []

    client = _get_client()
    data_source_id = _get_data_source_id(client, db_id)
    if not data_source_id:
        return []

    regions: list[tuple[str, str]] = []

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
            name = _extract_rich_text(props, "Region Name").strip()
            if code:
                regions.append((code, name or code))

        has_more = resp.get("has_more", False)
        start_cursor = resp.get("next_cursor")

    return regions


def resolve_region_page_id(
    region_value: str | None,
    code_to_page_id: Optional[dict[str, str]] = None,
    alias_to_page_id: Optional[dict[str, str]] = None,
) -> Optional[str]:
    """
    Resolve a region value to a Regions DB page id.

    region_value can be:
      - Canonical code: "US", "GB", "CIS", "MENA", "XF", "XL"
      - Adobe code: "sa_en", "cis_en", "africa", "la"
      - Adobe name: "Saudi Arabia - English", "Danmark", "台灣地區", etc. (must exist in Aliases)
    """
    if not region_value:
        return None
    raw = region_value.strip()
    if not raw:
        return None

    code_to_page_id = code_to_page_id or {}
    alias_to_page_id = alias_to_page_id or {}

    lower = raw.lower()
    canonical_override = _VALUE_TO_CANONICAL_OVERRIDES.get(lower)
    if canonical_override:
        return code_to_page_id.get(canonical_override) or alias_to_page_id.get(canonical_override.lower())

    # Direct code match (supports 2-4 letter codes like CIS/MENA/XF/XL)
    direct = code_to_page_id.get(raw.upper())
    if direct:
        return direct

    # Alias match (case-insensitive)
    alias = alias_to_page_id.get(lower)
    if alias:
        return alias

    # Heuristic: Adobe codes like "sa_en" -> "SA"
    if len(lower) >= 2 and "_" in lower:
        maybe = lower[:2].upper()
        return code_to_page_id.get(maybe)

    return None

