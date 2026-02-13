"""
Notion API client for pushing scraped pricing data.

Follows the error handling and configuration patterns from myapp/PriceDuck/api.py.
"""

import os
from datetime import datetime
from typing import Optional

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


def push_price_data(
    product_name: str,
    amount: float,
    currency: str,
    period: str,
    plan_name: Optional[str] = None,
    source_url: Optional[str] = None,
    success: bool = True,
    notes: Optional[str] = None,
    region_page_id: Optional[str] = None,
    region_relation_property: str = "Region Relation",
) -> None:
    """
    Create a new row in the Scraped Pricing Notion database.

    Database properties (actual names in Notion):
    - Scraped Timestamp (Title) - uses product_name + timestamp
    - Product (Select) - product name
    - Amount (Number)
    - Currency (Select)
    - Period (Select)
    - Page Link (URL) - source URL
    - Region Relation (Relation) - link to Regions DB
    """
    client = get_notion_client()

    db_id = os.getenv("NOTION_SCRAPED_PRICING_DB_ID")
    if not db_id or not db_id.strip():
        raise ValueError(
            "NOTION_SCRAPED_PRICING_DB_ID environment variable is not set. "
            "Use the database ID from your Notion Scraped Pricing database URL."
        )

    # Format timestamp to match existing entries (microseconds included)
    scraped_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")

    properties: dict = {
        "Scraped Timestamp": {"title": [{"text": {"content": scraped_at}}]},
        "Amount": {"number": amount},
    }

    if product_name:
        properties["Product"] = {"select": {"name": product_name}}
    if currency:
        properties["Currency"] = {"select": {"name": currency}}
    if period:
        properties["Period"] = {"select": {"name": period}}
    if source_url:
        properties["Page Link"] = {"url": source_url}
    if region_page_id:
        properties[region_relation_property] = {"relation": [{"id": region_page_id}]}

    try:
        client.pages.create(
            parent={"database_id": db_id.strip()},
            properties=properties,
        )
    except APIResponseError as e:
        # Handle both old (e.message) and new (str(e)) versions of notion-client
        error_msg = getattr(e, 'message', str(e))
        raise ValueError(
            f"Notion API error: {error_msg}. "
            "Ensure your integration has access to the database."
        )
    except Exception as e:
        raise ValueError(f"Failed to push data to Notion: {str(e)}")
