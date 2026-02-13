#!/usr/bin/env python3
"""
Selector Discovery CLI — Discovers CSS selectors for products in the Products DB.

Uses Gemini API to analyze pricing pages and extract CSS selectors.

Usage:
  python -m scrapers.selector_discovery           # Discover for all products needing selectors
  python -m scrapers.selector_discovery --url URL # Discover for a single URL
"""

import argparse
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Optional

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


def _ts() -> str:
    """Return timestamp for logging."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fetch_html_requests(url: str) -> str:
    """Fetch page HTML using requests (static sites)."""
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.text


def fetch_page_with_screenshot(url: str, use_stealth: bool = False) -> tuple[str, bytes]:
    """Fetch page HTML and screenshot using Playwright. Returns (html, png_bytes)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ValueError(
            "Playwright is not installed. Run: pip install playwright && playwright install chromium"
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
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.fragment:
            try:
                el = page.query_selector(f"#{parsed.fragment}")
                if el:
                    el.scroll_into_view_if_needed()
            except Exception:
                pass
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            page.evaluate("window.scrollTo(0, 0)")
            if parsed.fragment:
                el = page.query_selector(f"#{parsed.fragment}")
                if el:
                    el.scroll_into_view_if_needed()
        except Exception:
            pass
        try:
            page.wait_for_function(
                """() => {
                    const text = document.body?.innerText || '';
                    return /\\$|€|£|¥|\\/month|\\/year|\\d+\\.\\d{2}/.test(text);
                }""",
                timeout=20000,
            )
        except Exception:
            pass
        from scrapers.progress import sleep_with_progress
        sleep_with_progress(random.uniform(5, 12), "Letting page settle")
        html = page.content()
        screenshot = page.screenshot(type="png")
        browser.close()
    return html, screenshot


def fetch_html_playwright(url: str, use_stealth: bool = False) -> str:
    """Fetch page HTML using Playwright (JS-rendered sites). Optionally use stealth mode."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ValueError(
            "Playwright is not installed. Run: pip install playwright && playwright install chromium"
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

        # Scroll to hash target (e.g. #pricing) to trigger lazy-loaded content
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if parsed.fragment:
            try:
                el = page.query_selector(f"#{parsed.fragment}")
                if el:
                    el.scroll_into_view_if_needed()
            except Exception:
                pass

        # Full-page scroll to trigger lazy-loaded content (common on SPAs like ChatGPT)
        try:
            page.evaluate("""() => {
                window.scrollTo(0, document.body.scrollHeight);
            }""")
            time.sleep(2)
            page.evaluate("""() => {
                window.scrollTo(0, 0);
            }""")
            if parsed.fragment:
                el = page.query_selector(f"#{parsed.fragment}")
                if el:
                    el.scroll_into_view_if_needed()
        except Exception:
            pass

        # Wait for price-like content to appear (SPAs often load pricing async)
        try:
            page.wait_for_function(
                """() => {
                    const text = document.body?.innerText || '';
                    return /\\$|€|£|¥|\\/month|\\/year|\\d+\\.\\d{2}/.test(text);
                }""",
                timeout=20000,
            )
        except Exception:
            pass

        from scrapers.progress import sleep_with_progress
        delay = random.uniform(5, 12)
        sleep_with_progress(delay, "Letting page settle")
        html = page.content()
        browser.close()
    return html


def fetch_html_playwright_stealth(url: str) -> str:
    """Fetch page HTML using Playwright with full stealth mode for bot protection."""
    return fetch_html_playwright(url, use_stealth=True)


def fetch_with_retry(
    url: str,
    use_js: bool = False,
    max_retries: int = 3,
) -> str:
    """
    Fetch HTML with automatic retry and stealth escalation.

    When use_js=False: requests -> Playwright -> Playwright stealth.
    When use_js=True: Playwright -> Playwright stealth (requests won't render JS).
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
                print(f"  Attempt {attempt + 1} failed, retrying with more stealth...")
                from scrapers.progress import sleep_with_progress
                sleep_with_progress(2**attempt, "Backoff before retry")
    if last_error:
        raise last_error
    raise RuntimeError("Fetch failed")


def discover_selectors_with_vision(
    screenshot: bytes,
    html: str,
    url: str,
    plan_name: str = "Plus",
) -> dict | None:
    """
    Use Gemini vision to analyze a screenshot + HTML and find price selectors.
    Returns updated selectors dict if found, None otherwise.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        return None
    try:
        import google.generativeai as genai
        import base64
    except ImportError:
        return None

    genai.configure(api_key=api_key.strip())
    model = genai.GenerativeModel("gemini-2.5-flash")

    html_preview = html[:80_000] + ("..." if len(html) > 80_000 else "")
    prompt = f"""You are analyzing a pricing page screenshot and its HTML to find CSS selectors for scraping.

**Goal**: Find a CSS selector that targets the NUMERIC PRICE AMOUNT (e.g. $20, 20, €19) for the "{plan_name}" plan.

**Instructions**:
1. Look at the screenshot - where is the price displayed for {plan_name}? What does it say?
2. Search the HTML for that price value or nearby text (e.g. "/month", plan name).
3. Identify the element containing the price - note its tag, class names, data attributes, parent structure.
4. Provide a CSS selector that would select that element.
5. If the price is NOT visible in the screenshot (e.g. placeholder, loading), say so and suggest: "try scrolling to the {plan_name} card" or "price may load via JavaScript".

Return ONLY valid JSON:
{{
  "price": "css selector or empty string",
  "currency": "css selector or empty string",
  "period": "css selector or empty string",
  "plan_name": "css selector or empty string",
  "note": "optional: what you saw or suggestion"
}}

If you cannot find the price, set price to "" and explain in note.

URL: {url}

HTML (excerpt):
{html_preview}
"""

    image_part = {
        "inline_data": {
            "mime_type": "image/png",
            "data": base64.b64encode(screenshot).decode("utf-8"),
        }
    }
    content = [{"parts": [image_part, {"text": prompt}]}]

    try:
        response = model.generate_content(
            content,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
    except (TypeError, AttributeError):
        response = model.generate_content(content, generation_config={"temperature": 0.1})

    text = response.text.strip()
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        text = json_match.group(1).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    selectors = {
        "price": parsed.get("price", ""),
        "currency": parsed.get("currency", ""),
        "period": parsed.get("period", ""),
        "plan_name": parsed.get("plan_name", ""),
    }
    if parsed.get("note"):
        selectors["_vision_note"] = parsed["note"]
    return selectors


def discover_selectors_with_gemini(html: str, url: str) -> dict:
    """Send HTML to Gemini and get JSON with CSS selectors and region switcher info."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Get your key from ai.google.dev or aistudio.google.com/apikey"
        )

    # Truncate HTML if too long (Gemini has context limits)
    max_chars = 200_000
    if len(html) > max_chars:
        html = html[:max_chars] + "\n<!-- ... HTML truncated ... -->"

    prompt = f"""Analyze this pricing page and extract:

1. **PRICING SELECTORS** (CSS selectors):
   - price: numeric amount (e.g., 19.99, 20). Target the element containing the number or full price.
   - currency: symbol or code (e.g., $, USD, €, EUR).
   - period: billing frequency (e.g., /month, monthly, per year, yearly, one-time).
   - plan_name: tier name (e.g., "Pro", "Basic", "Enterprise").

   For React/SPA sites: use data-testid, data-*, class names, or parent-child selectors. Prefer selectors that target unique text or structure. If multiple plans exist, pick selectors that match the first/main plan.

2. **REGION SWITCHER** (if present):
   - selector: CSS selector for the region switcher element (dropdown, button, or link).
   - type: "dropdown", "button", "url-param", or "none".
   - regions: List of region codes/names visible (e.g., ["US", "UK", "EU"]). Empty array if none.
   - url_pattern: If region is in URL params, provide template like "?country={{REGION}}" or "&region={{REGION}}". Empty string if N/A.

IMPORTANT: For pages that show pricing in tables or cards, look for the first/main plan. Use class names, data-testid, or structural selectors (e.g. nth-of-type, :first-of-type). If pricing is in a different format (e.g. "From $20/month"), capture that element.

Return ONLY a valid JSON object with this exact structure:
{{
  "price": "selector or empty string",
  "currency": "selector or empty string",
  "period": "selector or empty string",
  "plan_name": "selector or empty string",
  "region_switcher": {{
    "selector": "selector or empty string",
    "type": "dropdown|button|url-param|none",
    "regions": ["US", "UK", ...],
    "url_pattern": "template or empty string"
  }}
}}

If no region switcher exists, set region_switcher.type to "none" and regions to [].

Page URL: {url}

HTML:
{html}
"""

    try:
        import google.generativeai as genai
    except ImportError:
        raise ValueError(
            "google-generativeai is not installed. Run: pip install google-generativeai"
        )

    genai.configure(api_key=api_key.strip())
    model = genai.GenerativeModel("gemini-2.5-flash")

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
    except (TypeError, AttributeError):
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1},
        )

    text = response.text.strip()
    # Extract JSON if wrapped in markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if json_match:
        text = json_match.group(1).strip()
    parsed = json.loads(text)

    required = ["price", "currency", "period", "plan_name"]
    for k in required:
        if k not in parsed:
            parsed[k] = ""
        elif not isinstance(parsed[k], str):
            parsed[k] = str(parsed[k]) if parsed[k] else ""

    # Normalize region_switcher
    rs = parsed.get("region_switcher") or {}
    if not isinstance(rs, dict):
        rs = {}
    parsed["region_switcher"] = {
        "selector": rs.get("selector") or "",
        "type": rs.get("type") or "none",
        "regions": rs.get("regions") if isinstance(rs.get("regions"), list) else [],
        "url_pattern": rs.get("url_pattern") or "",
    }
    if parsed["region_switcher"]["type"] == "none":
        parsed["region_switcher"]["regions"] = []
        parsed["region_switcher"]["selector"] = ""
        parsed["region_switcher"]["url_pattern"] = ""

    return parsed


def test_selectors(html: str, selectors: dict) -> dict:
    """Test selectors against HTML and return extracted values."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    results: dict[str, str] = {}
    for key, sel in selectors.items():
        if not sel:
            results[key] = "(no selector)"
            continue
        try:
            el = soup.select_one(sel)
            results[key] = el.get_text(strip=True) if el else "(not found)"
        except Exception as e:
            results[key] = f"(error: {e})"
    return results


def discover_for_product(
    product: dict,
    use_js: bool = False,
    no_test: bool = False,
    write_to_notion: bool = True,
    save_html_path: Optional[str] = None,
) -> bool:
    """
    Run discovery for a single product.

    Returns True if successful, False otherwise.
    """
    from scrapers.products_client import update_product_selectors

    name = product.get("name", "Unknown")
    url = product.get("url", "")
    page_id = product.get("page_id", "")
    existing_rendering = product.get("rendering", "static")

    # Determine rendering mode
    rendering = "js" if use_js else existing_rendering

    print(f"\n[{_ts()}] Processing: {name}")
    print(f"  URL: {url}")

    # chatgpt.com/#pricing redirects to login; openai.com often works better for scraping
    if "chatgpt.com" in url:
        url = "https://openai.com/chatgpt/pricing"
        print(f"  (Using {url} - better availability for ChatGPT pricing)")

    from scrapers.progress import spinner
    try:
        if rendering == "js":
            print(f"  Fetching with Playwright (JS rendering)...")
            with spinner("Loading page (may take 30–60s for JS sites)..."):
                html = fetch_with_retry(url, use_js=True)
        else:
            print(f"  Fetching with requests (static)...")
            html = fetch_with_retry(url, use_js=False)
    except Exception as e:
        print(f"  Error fetching page: {e}")
        print("  Tip: Try --js if the page requires JavaScript to render.")
        return False

    try:
        with spinner("Sending to Gemini for selector discovery..."):
            selectors = discover_selectors_with_gemini(html, url)

        # Vision fallback: when price selector empty or test returns no value
        pricing_selectors = {k: v for k, v in selectors.items() if k != "region_switcher" and isinstance(v, str)}
        test_vals = test_selectors(html, pricing_selectors)
        price_val = test_vals.get("price", "")
        price_ok = price_val and price_val not in ("(not found)", "(no selector)", "(error:")
        if not selectors.get("price") or not price_ok:
            print(f"  (Price not found - trying Gemini vision on page screenshot...)")
            try:
                with spinner("Capturing screenshot and analyzing with vision..."):
                    html_vision, screenshot = fetch_page_with_screenshot(url, use_stealth=True)
                    plan_hint = name if "ChatGPT" in name or "Plus" in name else "main paid plan"
                    if "Plus" in plan_hint or "ChatGPT" in plan_hint:
                        plan_hint = "Plus"
                    vision_result = discover_selectors_with_vision(
                        screenshot, html_vision, url, plan_name=plan_hint
                    )
                if vision_result and vision_result.get("price"):
                    selectors["price"] = vision_result.get("price", "")
                    if vision_result.get("currency"):
                        selectors["currency"] = vision_result.get("currency", "")
                    if vision_result.get("_vision_note"):
                        print(f"  Vision note: {vision_result['_vision_note'][:80]}")
                    html = html_vision  # use fresh HTML for testing
            except Exception as e:
                print(f"  Vision fallback failed: {e}")

        # Fallback: chatgpt.com often has hard-to-parse structure; try openai.com
        if not selectors.get("price") and "chatgpt.com" in url:
            alt_url = "https://openai.com/chatgpt/pricing"
            print(f"  (chatgpt.com returned no selectors - trying {alt_url}...)")
            try:
                if rendering == "js":
                    with spinner("Loading OpenAI pricing page..."):
                        html_alt = fetch_with_retry(alt_url, use_js=True)
                else:
                    html_alt = fetch_with_retry(alt_url, use_js=False)
                selectors = discover_selectors_with_gemini(html_alt, alt_url)
                if selectors.get("price"):
                    print(f"  Found selectors from openai.com")
                    url = alt_url  # for region_switcher context
            except Exception as e:
                print(f"  Fallback failed: {e}")
    except Exception as e:
        print(f"  Error from Gemini: {e}")
        return False

    print(f"  Discovered selectors:")
    region_switcher = selectors.pop("region_switcher", None) or {}
    for k, v in selectors.items():
        print(f"    {k}: {v or '(none)'}")

    # Save HTML for debugging when no price selector found
    if not selectors.get("price") and (save_html_path or "chatgpt.com" in url):
        path = save_html_path or (Path(__file__).parent / "debug_capture.html")
        try:
            path = Path(path)
            path.write_text(html, encoding="utf-8")
            print(f"  (No price selector found - HTML saved to {path} for debugging)")
            if "chatgpt.com" in url:
                print(f"  Tip: Try https://openai.com/chatgpt/pricing if this URL fails")
        except Exception:
            pass
    if region_switcher.get("type") and region_switcher["type"] != "none":
        print(f"  Region switcher: type={region_switcher.get('type')}, regions={region_switcher.get('regions', [])}")

    if not no_test:
        print(f"  Test results (extracted values):")
        test_results = test_selectors(html, selectors)
        for k, v in test_results.items():
            preview = (v[:50] + "…") if len(str(v)) > 50 else v
            print(f"    {k}: {preview}")

    # Write to Notion if we have a page_id
    if write_to_notion and page_id:
        try:
            region_config = None
            if region_switcher and region_switcher.get("type") != "none":
                region_config = {
                    "selector": region_switcher.get("selector", ""),
                    "type": region_switcher.get("type", "none"),
                    "regions": region_switcher.get("regions", []),
                    "url_pattern": region_switcher.get("url_pattern", ""),
                }
            update_product_selectors(page_id, selectors, rendering, region_config)
            print(f"  Saved selectors to Notion")
        except Exception as e:
            print(f"  Error saving to Notion: {e}")
            return False
    elif not page_id:
        print(f"  (No page_id - selectors not saved to Notion)")

    return True


def discover_for_url(
    url: str,
    use_js: bool = False,
    no_test: bool = False,
    product_name: str = "",
    save_html_path: Optional[str] = None,
) -> int:
    """
    Run discovery for a single URL.

    If a matching product exists in Notion, update it. Otherwise, print JSON config.
    """
    from scrapers.products_client import find_product_by_url

    print(f"[{_ts()}] Looking up URL in Products DB...")
    try:
        product = find_product_by_url(url)
    except Exception as e:
        print(f"[{_ts()}] Warning: Could not query Notion: {e}")
        product = None

    if product:
        print(f"[{_ts()}] Found product: {product['name']}")
        success = discover_for_product(
            product,
            use_js=use_js,
            no_test=no_test,
            write_to_notion=True,
            save_html_path=save_html_path,
        )
        return 0 if success else 1
    else:
        print(f"[{_ts()}] No matching product found in Notion. Running discovery only...")

        # Fetch and discover
        from scrapers.progress import spinner
        print(f"[{_ts()}] Fetching: {url}")
        try:
            with spinner("Loading page (may take 30–60s for JS sites)..." if use_js else "Fetching..."):
                html = fetch_with_retry(url, use_js=use_js)
        except Exception as e:
            print(f"[{_ts()}] Error fetching page: {e}")
            print("Tip: Try --js if the page requires JavaScript to render.")
            return 1

        try:
            with spinner("Sending to Gemini for selector discovery..."):
                selectors = discover_selectors_with_gemini(html, url)
        except Exception as e:
            print(f"[{_ts()}] Error from Gemini: {e}")
            return 1

        region_switcher = selectors.pop("region_switcher", None) or {}
        print("\n--- Discovered selectors ---")
        for k, v in selectors.items():
            print(f"  {k}: {v or '(none)'}")
        if region_switcher.get("type") and region_switcher["type"] != "none":
            print(f"  Region switcher: type={region_switcher.get('type')}, regions={region_switcher.get('regions', [])}")

        if not selectors.get("price") and (save_html_path or "chatgpt.com" in url):
            path = save_html_path or (Path(__file__).parent / "debug_capture.html")
            try:
                Path(path).write_text(html, encoding="utf-8")
                print(f"\n  (No price selector - HTML saved to {path})")
                if "chatgpt.com" in url:
                    print(f"  Tip: Try https://openai.com/chatgpt/pricing instead")
            except Exception:
                pass

        if not no_test:
            print("\n--- Test results (extracted values) ---")
            test_results = test_selectors(html, selectors)
            for k, v in test_results.items():
                preview = (v[:60] + "…") if len(str(v)) > 60 else v
                print(f"  {k}: {preview}")

        # Build product name from URL if not provided
        if not product_name:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.replace("www.", "")
            product_name = domain.split(".")[0].title()

        print("\n--- To add this product ---")
        print("1. Add a row to the Products DB in Notion with:")
        print(f"   - Product Name: {product_name}")
        print(f"   - Product URL: {url}")
        print("2. Run: python -m scrapers.selector_discovery")
        print("\nOr manually add these selectors to the Products DB:")
        output = {"selectors": selectors, "rendering": rendering}
        if region_switcher and region_switcher.get("type") != "none":
            output["region_config"] = region_switcher
        print(json.dumps(output, indent=2))

        return 0


def discover_all(save_html_path: Optional[str] = None) -> int:
    """
    Discover selectors for all products in Notion that need them.

    Returns exit code (0 = success, 1 = some failures).
    """
    from scrapers.products_client import load_products_for_discovery

    print(f"[{_ts()}] Loading products needing discovery from Notion...")
    try:
        products = load_products_for_discovery()
    except Exception as e:
        print(f"[{_ts()}] Error loading products: {e}")
        return 1

    if not products:
        print(f"[{_ts()}] No products need discovery. All products have selectors or no URL.")
        return 0

    print(f"[{_ts()}] Found {len(products)} product(s) needing discovery")

    success_count = 0
    failure_count = 0

    for product in products:
        # Use Rendering field from Notion, fallback to static
        use_js = (product.get("rendering", "static") == "js")
        ok = discover_for_product(
            product,
            use_js=use_js,
            no_test=False,
            write_to_notion=True,
            save_html_path=save_html_path,
        )
        if ok:
            success_count += 1
        else:
            failure_count += 1

    print(f"\n[{_ts()}] Done. Succeeded: {success_count}, Failed: {failure_count}")
    return 0 if failure_count == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Discover CSS selectors for products using Gemini AI"
    )
    parser.add_argument(
        "--url",
        default="",
        help="Single URL to discover selectors for (optional)",
    )
    parser.add_argument(
        "--js",
        action="store_true",
        help="Use Playwright for JS-rendered pages",
    )
    parser.add_argument(
        "--name",
        default="",
        help="Product name (only used with --url for output)",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip testing selectors against the page",
    )
    parser.add_argument(
        "--save-html",
        metavar="PATH",
        default="",
        help="Save captured HTML to file when no price selector found (for debugging)",
    )
    args = parser.parse_args()

    save_html = args.save_html.strip() or None

    if args.url:
        return discover_for_url(
            url=args.url.strip(),
            use_js=args.js,
            no_test=args.no_test,
            product_name=args.name,
            save_html_path=save_html,
        )
    else:
        return discover_all(save_html_path=save_html)


if __name__ == "__main__":
    sys.exit(main())
