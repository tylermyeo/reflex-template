"""
Notion API client for the Products database.

Provides functions to load products for discovery/scraping and update selector values.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from notion_client import Client
    from notion_client.errors import APIResponseError
except ImportError:
    Client = None
    APIResponseError = Exception  # type: ignore


def get_notion_client() -> "Client":
    """Initialize and return Notion client with error handling."""
    if Client is None:
        raise ValueError(
            "notion-client is not installed. Run: pip install notion-client"
        )

    token = os.getenv("NOTION_TOKEN")
    if not token or not token.strip():
        raise ValueError(
            "NOTION_TOKEN environment variable is not set. "
            "Get your integration token from notion.so/my-integrations"
        )

    try:
        client = Client(auth=token)
        return client
    except Exception as e:
        raise ValueError(f"Failed to initialize Notion client: {str(e)}")


def _get_products_db_id() -> str:
    """Get the Products database ID from environment."""
    db_id = os.getenv("NOTION_PRODUCTS_DB_ID")
    if not db_id or not db_id.strip():
        raise ValueError(
            "NOTION_PRODUCTS_DB_ID environment variable is not set. "
            "Set it to your Products database ID."
        )
    return db_id.strip()


def _get_products_data_source_id(client: "Client") -> str:
    """Get the first data source ID from the Products database."""
    db_id = os.getenv("NOTION_PRODUCTS_DB_ID")
    if not db_id or not db_id.strip():
        raise ValueError(
            "NOTION_PRODUCTS_DB_ID environment variable is not set. "
            "Set it to your Products database ID (e.g., 0809cffb842e44a5a69f96f7b653de33)"
        )
    
    try:
        # Retrieve database to get data source IDs
        database = client.databases.retrieve(database_id=db_id.strip())
        data_sources = database.get("data_sources", [])
        
        if not data_sources:
            raise ValueError(
                f"No data sources found in database {db_id}. "
                "The database may be empty or not properly configured."
            )
        
        # Return the first data source ID
        return data_sources[0]["id"]
    
    except APIResponseError as e:
        raise ValueError(
            f"Failed to retrieve database {db_id}: {str(e)}. "
            "Ensure your integration has access to the Products database."
        ) from e


def _extract_text_property(props: dict, name: str) -> str:
    """Extract text from a rich_text or title property."""
    prop = props.get(name, {})
    prop_type = prop.get("type", "")

    if prop_type == "title":
        title_arr = prop.get("title", [])
        return "".join(t.get("plain_text", "") for t in title_arr)
    elif prop_type == "rich_text":
        text_arr = prop.get("rich_text", [])
        return "".join(t.get("plain_text", "") for t in text_arr)
    return ""


def _extract_url_property(props: dict, name: str) -> str:
    """Extract URL from a url property."""
    prop = props.get(name, {})
    if prop.get("type") == "url":
        return prop.get("url") or ""
    return ""


def _extract_select_property(props: dict, name: str) -> str:
    """Extract select option name from a select property."""
    prop = props.get(name, {})
    if prop.get("type") == "select":
        select_val = prop.get("select")
        if select_val:
            return select_val.get("name", "")
    return ""


def _parse_available_regions(regions_str: str) -> list[str]:
    """Parse Available Regions from JSON string or comma-separated list."""
    if not regions_str or not regions_str.strip():
        return []
    s = regions_str.strip()
    if s.startswith("["):
        try:
            parsed = json.loads(s)
            return [str(r).strip() for r in parsed if r]
        except (json.JSONDecodeError, TypeError):
            pass
    return [r.strip() for r in s.split(",") if r.strip()]


def _page_to_product(page: dict) -> dict[str, Any]:
    """Convert a Notion page object to a product dict."""
    props = page.get("properties", {})
    page_id = page.get("id", "")

    name = _extract_text_property(props, "Product Name")
    url = _extract_url_property(props, "Product URL")
    rendering = _extract_select_property(props, "Rendering") or "static"

    selectors = {
        "price": _extract_text_property(props, "Selector Price"),
        "currency": _extract_text_property(props, "Selector Currency"),
        "period": _extract_text_property(props, "Selector Period"),
        "plan_name": _extract_text_property(props, "Selector Plan Name"),
    }

    # Region switcher config
    region_switcher_selector = _extract_text_property(props, "Region Switcher Selector")
    region_switcher_type = _extract_select_property(props, "Region Switcher Type") or "none"
    available_regions_str = _extract_text_property(props, "Available Regions")
    region_url_pattern = _extract_text_property(props, "Region URL Pattern")

    regions = _parse_available_regions(available_regions_str)
    region_config = {
        "selector": region_switcher_selector,
        "type": region_switcher_type,
        "regions": regions,
        "url_pattern": region_url_pattern,
    }

    return {
        "page_id": page_id,
        "name": name,
        "url": url,
        "rendering": rendering,
        "selectors": selectors,
        "region_config": region_config,
    }


def load_products_for_discovery() -> list[dict[str, Any]]:
    """
    Load products that need selector discovery.

    Returns products where Product URL is set but Selector Price is empty.
    """
    client = get_notion_client()
    data_source_id = _get_products_data_source_id(client)

    # Filter: Product URL is not empty AND Selector Price is empty
    filter_obj = {
        "and": [
            {"property": "Product URL", "url": {"is_not_empty": True}},
            {"property": "Selector Price", "rich_text": {"is_empty": True}},
        ]
    }

    try:
        results = []
        has_more = True
        start_cursor = None

        while has_more:
            response = client.data_sources.query(
                data_source_id=data_source_id,
                filter=filter_obj,
                start_cursor=start_cursor,
            )
            for page in response.get("results", []):
                product = _page_to_product(page)
                if product["name"] and product["url"]:
                    results.append(product)

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return results

    except APIResponseError as e:
        raise ValueError(
            f"Notion API error: {str(e)}. "
            "Ensure your integration has access to the Products database."
        )
    except Exception as e:
        raise ValueError(f"Failed to query Products database: {str(e)}")


def load_products_for_scraping() -> list[dict[str, Any]]:
    """
    Load products that are ready for scraping.

    Returns products where Selector Price is set (has selectors).
    """
    client = get_notion_client()
    data_source_id = _get_products_data_source_id(client)

    # Filter: Selector Price is not empty
    filter_obj = {
        "property": "Selector Price",
        "rich_text": {"is_not_empty": True},
    }

    try:
        results = []
        has_more = True
        start_cursor = None

        while has_more:
            response = client.data_sources.query(
                data_source_id=data_source_id,
                filter=filter_obj,
                start_cursor=start_cursor,
            )
            for page in response.get("results", []):
                product = _page_to_product(page)
                if product["name"] and product["url"]:
                    results.append(product)

            has_more = response.get("has_more", False)
            start_cursor = response.get("next_cursor")

        return results

    except APIResponseError as e:
        raise ValueError(
            f"Notion API error: {str(e)}. "
            "Ensure your integration has access to the Products database."
        )
    except Exception as e:
        raise ValueError(f"Failed to query Products database: {str(e)}")


def update_product_selectors(
    page_id: str,
    selectors: dict[str, str],
    rendering: Optional[str] = None,
    region_config: Optional[dict] = None,
) -> None:
    """
    Update a product page with discovered selectors and optional region config.

    Args:
        page_id: The Notion page ID to update
        selectors: Dict with keys: price, currency, period, plan_name
        rendering: Optional rendering mode ("static" or "js")
        region_config: Optional dict with selector, type, regions, url_pattern
    """
    client = get_notion_client()

    properties: dict = {}

    if selectors.get("price"):
        properties["Selector Price"] = {
            "rich_text": [{"type": "text", "text": {"content": selectors["price"]}}]
        }
    if selectors.get("currency"):
        properties["Selector Currency"] = {
            "rich_text": [{"type": "text", "text": {"content": selectors["currency"]}}]
        }
    if selectors.get("period"):
        properties["Selector Period"] = {
            "rich_text": [{"type": "text", "text": {"content": selectors["period"]}}]
        }
    if selectors.get("plan_name"):
        properties["Selector Plan Name"] = {
            "rich_text": [{"type": "text", "text": {"content": selectors["plan_name"]}}]
        }
    if rendering:
        properties["Rendering"] = {"select": {"name": rendering}}

    if region_config:
        if region_config.get("selector"):
            properties["Region Switcher Selector"] = {
                "rich_text": [{"type": "text", "text": {"content": region_config["selector"][:2000]}}]
            }
        if region_config.get("type"):
            properties["Region Switcher Type"] = {
                "select": {"name": region_config["type"]}
            }
        if region_config.get("regions"):
            regions_str = json.dumps(region_config["regions"]) if isinstance(
                region_config["regions"], list
            ) else str(region_config["regions"])
            properties["Available Regions"] = {
                "rich_text": [{"type": "text", "text": {"content": regions_str[:2000]}}]
            }
        if region_config.get("url_pattern"):
            properties["Region URL Pattern"] = {
                "rich_text": [{"type": "text", "text": {"content": region_config["url_pattern"][:2000]}}]
            }

    if not properties:
        return  # Nothing to update

    try:
        client.pages.update(page_id=page_id, properties=properties)
    except APIResponseError as e:
        raise ValueError(
            f"Notion API error updating product: {e.message}. "
            "Ensure your integration has access to the Products database."
        )
    except Exception as e:
        raise ValueError(f"Failed to update product in Notion: {str(e)}")


def find_product_by_url(url: str) -> Optional[dict[str, Any]]:
    """
    Find a product by its Product URL.

    Returns the product dict if found, None otherwise.
    """
    client = get_notion_client()
    db_id = _get_products_db_id()

    filter_obj = {"property": "Product URL", "url": {"equals": url}}

    try:
        response = client.databases.query(database_id=db_id, filter=filter_obj)
        results = response.get("results", [])
        if results:
            return _page_to_product(results[0])
        return None

    except APIResponseError as e:
        raise ValueError(f"Notion API error: {e.message}")
    except Exception as e:
        raise ValueError(f"Failed to query Products database: {str(e)}")
