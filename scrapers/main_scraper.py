#!/usr/bin/env python3
"""
Main Scraper — Fetches pricing from products in the Notion Products DB and pushes to Scraped Pricing.

Run manually: python -m scrapers.main_scraper
"""

import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# Load .env from project root
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add project root to path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from bs4 import BeautifulSoup

from scrapers.notion_client import push_price_data
from scrapers.products_client import load_products_for_scraping
from scrapers.regions import ensure_regions_cache, resolve_region_page_id
from scrapers.regions import ensure_regions_cache


def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


LOGS_DIR = Path(__file__).resolve().parent / "logs"


def load_products() -> list[dict[str, Any]]:
    """Load products from Notion Products DB that have selectors configured."""
    try:
        products = load_products_for_scraping()
        # Validate that each product has the required selector
        valid = []
        for p in products:
            selectors = p.get("selectors", {})
            if not selectors.get("price"):
                print(f"[{_ts()}] Skipping {p.get('name', 'Unknown')}: missing price selector")
                continue
            valid.append(p)
        return valid
    except Exception as e:
        print(f"[{_ts()}] Error loading products from Notion: {e}")
        return []


def fetch_html_requests(url: str) -> str:
    """Fetch page HTML using requests (static sites)."""
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_html_playwright(url: str, use_stealth: bool = False) -> str:
    """Fetch page HTML using Playwright (JS-rendered sites). Optionally use stealth mode."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ValueError(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )
    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        if use_stealth:
            try:
                from playwright_stealth import Stealth
                Stealth().apply_stealth_sync(page)
            except Exception:
                pass
        page.goto(url, wait_until="load", timeout=60000)
        from scrapers.progress import sleep_with_progress
        sleep_with_progress(random.uniform(2, 5), "Letting page settle")
        html = page.content()
        browser.close()
    return html


def fetch_html_playwright_stealth(url: str) -> str:
    """Fetch page HTML using Playwright with full stealth mode for bot protection."""
    return fetch_html_playwright(url, use_stealth=True)


def fetch_with_retry(url: str, use_js: bool = False, max_retries: int = 3) -> str:
    """
    Fetch HTML with automatic retry and stealth escalation.
    When use_js=False: requests -> Playwright -> Playwright stealth.
    When use_js=True: Playwright -> Playwright stealth.
    """
    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            if attempt == 0 and not use_js:
                return fetch_html_requests(url)
            elif attempt == 0 and use_js:
                return fetch_html_playwright(url, use_stealth=False)
            elif attempt == 1 and not use_js:
                return fetch_html_playwright(url, use_stealth=False)
            else:
                return fetch_html_playwright_stealth(url)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                from scrapers.progress import sleep_with_progress
                sleep_with_progress(2**attempt, "Backoff before retry")
    if last_error:
        raise last_error
    raise RuntimeError("Fetch failed")


def extract_text(soup: BeautifulSoup, selector: str) -> str:
    """Extract text from first element matching selector."""
    if not selector:
        return ""
    el = soup.select_one(selector)
    return el.get_text(strip=True) if el else ""


def parse_price(raw: str) -> Optional[float]:
    """Parse price string to float. Handles $19.99, 19,99 €, USD 19.99, etc."""
    if not raw or not isinstance(raw, str):
        return None
    # Remove currency symbols and common text
    cleaned = re.sub(r"[$€£¥₹]", "", raw)
    cleaned = re.sub(r"\b(USD|EUR|GBP|CAD|AUD)\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[\s,]", "", cleaned)
    # Handle European format (19,99 -> 19.99)
    if re.search(r"^\d{1,3}(,\d{3})*(\.\d+)?$", cleaned):
        cleaned = cleaned.replace(",", "")
    elif re.search(r"^\d+,\d{2}$", cleaned):
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def scrape_single_region(
    product: dict[str, Any],
    url: Optional[str] = None,
    region: Optional[str] = None,
) -> tuple[bool, str, Optional[dict]]:
    """
    Scrape one product at a single URL/region.
    Returns (success, message, data_dict or None).
    """
    name = product.get("name", "Unknown")
    base_url = product.get("url", "")
    url = url or base_url
    # ChatGPT: openai.com works better than chatgpt.com for scraping
    if "chatgpt.com" in url:
        url = "https://openai.com/chatgpt/pricing"
    rendering = product.get("rendering", "static")
    selectors = product.get("selectors", {})

    try:
        html = fetch_with_retry(url, use_js=(rendering == "js"))
    except Exception as e:
        return False, str(e), None

    soup = BeautifulSoup(html, "lxml")

    price_raw = extract_text(soup, selectors.get("price", ""))
    currency_raw = extract_text(soup, selectors.get("currency", ""))
    period_raw = extract_text(soup, selectors.get("period", ""))
    plan_name_raw = extract_text(soup, selectors.get("plan_name", ""))

    # Fallback: when price loads dynamically (e.g. ChatGPT), try parent of period element
    if not price_raw and period_raw and selectors.get("period"):
        period_el = soup.select_one(selectors["period"])
        if period_el and period_el.parent:
            parent_text = period_el.parent.get_text(strip=True)
            if re.search(r"[\$€£]?\s*\d+(?:\.\d{2})?", parent_text):
                price_raw = parent_text

    amount = parse_price(price_raw)
    if amount is None and price_raw:
        try:
            import pandas as pd
            amount = pd.to_numeric(re.sub(r"[^\d.]", "", price_raw), errors="coerce")
            amount = float(amount) if pd.notna(amount) else None
        except Exception:
            pass

    currency = (currency_raw or "USD").strip() or "USD"
    period = (period_raw or "").strip() or "Unknown"
    plan_name = (plan_name_raw or "").strip() or name

    currency = currency.replace(",", "").strip()
    period = period.replace(",", "").strip()

    data = {
        "product_name": name,
        "amount": amount,
        "currency": currency,
        "period": period,
        "plan_name": plan_name,
        "source_url": url,
        "region": region,
    }
    return True, "", data


def scrape_with_region_interaction(
    product: dict[str, Any],
    region: str,
) -> tuple[bool, str, Optional[dict]]:
    """
    Use Playwright to switch region via dropdown/button and scrape.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "Playwright not installed", None

    try:
        from playwright_stealth import Stealth
        stealth_apply = lambda p: Stealth().apply_stealth_sync(p)
    except Exception:
        stealth_apply = None

    name = product.get("name", "Unknown")
    url = product.get("url", "")
    selectors = product.get("selectors", {})
    region_config = product.get("region_config", {})
    switcher_sel = region_config.get("selector", "")
    switcher_type = region_config.get("type", "none")

    if not switcher_sel or switcher_type not in ("dropdown", "button"):
        return False, "No region switcher configured", None

    user_agent = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        if stealth_apply:
            try:
                stealth_apply(page)
            except Exception:
                pass
        page.goto(url, wait_until="load", timeout=60000)
        from scrapers.progress import sleep_with_progress
        sleep_with_progress(random.uniform(2, 5), "Page loading")

        try:
            page.click(switcher_sel)
            sleep_with_progress(random.uniform(0.5, 1.5), "Opening region menu")
            # Try to click region option: common patterns
            region_sel = f"text={region}"
            try:
                page.click(region_sel, timeout=3000)
            except Exception:
                region_sel = f"[data-region='{region}'], [data-value='{region}'], [data-country='{region}']"
                try:
                    page.click(region_sel, timeout=3000)
                except Exception:
                    pass
            sleep_with_progress(random.uniform(2, 4), "Waiting for prices to update")
        except Exception as e:
            browser.close()
            return False, f"Region switch failed: {e}", None

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "lxml")
    price_raw = extract_text(soup, selectors.get("price", ""))
    currency_raw = extract_text(soup, selectors.get("currency", ""))
    period_raw = extract_text(soup, selectors.get("period", ""))
    plan_name_raw = extract_text(soup, selectors.get("plan_name", ""))

    amount = parse_price(price_raw)
    if amount is None and price_raw:
        try:
            import pandas as pd
            amount = pd.to_numeric(re.sub(r"[^\d.]", "", price_raw), errors="coerce")
            amount = float(amount) if pd.notna(amount) else None
        except Exception:
            pass

    currency = (currency_raw or "USD").strip() or "USD"
    period = (period_raw or "").strip() or "Unknown"
    plan_name = (plan_name_raw or "").strip() or name
    currency = currency.replace(",", "").strip()
    period = period.replace(",", "").strip()

    data = {
        "product_name": name,
        "amount": amount,
        "currency": currency,
        "period": period,
        "plan_name": plan_name,
        "source_url": url,
        "region": region,
    }
    return True, "", data


def scrape_product_all_regions(product: dict[str, Any]) -> list[dict]:
    """
    Scrape a product across all its regions.
    Returns list of data dicts (one per region, or one for single-region).
    """
    results: list[dict] = []
    region_config = product.get("region_config", {}) or {}
    regions = region_config.get("regions", []) or []
    switcher_type = region_config.get("type", "none")
    url_pattern = region_config.get("url_pattern", "")

    if switcher_type == "none" or not regions:
        ok, err, data = scrape_single_region(product, region=None)
        if ok and data:
            results.append(data)
        return results

    for region in regions:
        try:
            if switcher_type == "url-param" and url_pattern:
                try:
                    url = url_pattern.replace("{{REGION}}", region).replace("{REGION}", region)
                    if url.startswith("?") or url.startswith("&"):
                        base = product.get("url", "")
                        sep = "&" if "?" in base else "?"
                        url = base + sep + (url[1:] if url[0] in "?&" else url)
                    elif not url.startswith("http"):
                        base = product.get("url", "")
                        url = base.rstrip("/") + ("/" if not url.startswith("/") else "") + url
                    ok, err, data = scrape_single_region(product, url=url, region=region)
                except Exception:
                    ok, err, data = scrape_with_region_interaction(product, region)
            elif switcher_type in ("dropdown", "button"):
                ok, err, data = scrape_with_region_interaction(product, region)
            else:
                ok, err, data = scrape_single_region(product, region=region)

            if ok and data:
                results.append(data)
            from scrapers.progress import sleep_with_progress
            sleep_with_progress(random.uniform(3, 7), f"Pause before next region")
        except Exception as e:
            continue
    return results


def scrape_product(product: dict[str, Any]) -> tuple[bool, str, list[dict]]:
    """
    Scrape one product (single or multi-region).
    Returns (success, error_message, list_of_data_dicts).
    """
    all_data = scrape_product_all_regions(product)
    if not all_data:
        return False, "No data extracted", []
    return True, "", all_data


def run_scraper() -> tuple[int, int]:
    """Run scraper for all products. Returns (success_count, failure_count)."""
    products = load_products()
    if not products:
        return 0, 0

    success_count = 0
    failure_count = 0

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"scrape_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_lines: list[str] = []

    def log(msg: str, also_print: bool = True) -> None:
        line = f"[{_ts()}] {msg}"
        log_lines.append(line)
        if also_print:
            print(line)

    log(f"Starting scraper for {len(products)} product(s)")
    code_to_page_id, alias_to_page_id = ensure_regions_cache()

    for i, product in enumerate(products):
        name = product.get("name", "Unknown")
        if i > 0:
            from scrapers.progress import sleep_with_progress
            sleep_with_progress(2, "Pause between products")

        try:
            from scrapers.progress import spinner
            with spinner(f"Scraping {name}..."):
                ok, err_msg, data_list = scrape_product(product)
            if not ok:
                log(f"✗ {name}: {err_msg}")
                failure_count += 1
                try:
                    push_price_data(
                        product_name=name,
                        amount=0.0,
                        currency="",
                        period="",
                        plan_name="",
                        source_url=product.get("url", ""),
                        success=False,
                        notes=err_msg,
                    )
                except Exception as push_err:
                    log(f"  (Failed to log error to Notion: {push_err})", also_print=False)
                continue

            if not data_list:
                log(f"✗ {name}: No data extracted")
                failure_count += 1
                continue

            for data in data_list:
                region_value = data.get("region")
                region_page_id = resolve_region_page_id(region_value, code_to_page_id, alias_to_page_id)
                if data.get("amount") is None:
                    try:
                        push_price_data(
                            product_name=name,
                            amount=0.0,
                            currency=data.get("currency", ""),
                            period=data.get("period", ""),
                            plan_name=data.get("plan_name", ""),
                            source_url=data.get("source_url", ""),
                            success=False,
                            notes="Could not parse price",
                            region_page_id=region_page_id,
                        )
                    except Exception as push_err:
                        log(f"  (Failed to log to Notion: {push_err})", also_print=False)
                    failure_count += 1
                else:
                    try:
                        push_price_data(
                            product_name=data["product_name"],
                            amount=data["amount"],
                            currency=data["currency"],
                            period=data["period"],
                            plan_name=data["plan_name"],
                            source_url=data.get("source_url"),
                            success=True,
                            region_page_id=region_page_id,
                        )
                        region_suffix = f" [{data['region']}]" if data.get("region") else ""
                        log(f"✓ {name}{region_suffix}: {data['amount']} {data['currency']} / {data['period']}")
                        success_count += 1
                    except Exception as e:
                        log(f"✗ {name}: Notion push failed: {e}")
                        failure_count += 1

        except Exception as e:
            log(f"✗ {name}: {e}")
            failure_count += 1

    log(f"\nDone. Succeeded: {success_count}, Failed: {failure_count}")

    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
        log(f"Log saved to {log_path}", also_print=False)
    except Exception:
        pass

    return success_count, failure_count


def main() -> int:
    try:
        success, failure = run_scraper()
        if success == 0 and failure == 0:
            return 1
        return 0 if failure == 0 else 1
    except KeyboardInterrupt:
        print(f"\n[{_ts()}] Interrupted by user")
        return 130
    except Exception as e:
        print(f"[{_ts()}] Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
