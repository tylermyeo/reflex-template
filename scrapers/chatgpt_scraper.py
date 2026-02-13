#!/usr/bin/env python3
"""
ChatGPT Plus Multi-Region Scraper

Scrapes ChatGPT Plus pricing across multiple regions.
Supports multiple modes:
  - Patchright mode (default): Uses patchright for stealth anti-bot bypass (FREE)
  - Direct mode: Uses Playwright with Geonode proxies (may be blocked)
  - Apify mode: Uses Apify's web scraper (costs compute credits)

Usage:
  python -m scrapers.chatgpt_scraper              # Uses patchright (recommended, FREE)
  python -m scrapers.chatgpt_scraper --direct     # Uses direct Playwright+proxy

Requirements:
  - patchright (for patchright mode - default)
  - GEONODE_USERNAME and GEONODE_PASSWORD in .env (for direct mode)
  - APIFY_TOKEN in .env (for Apify mode)
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

# Load .env
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
from scrapers.regions import ensure_regions_cache, resolve_region_page_id, fetch_all_regions


# Apify actors - web-scraper is free (compute only), cloudflare ones require monthly fee
APIFY_WEB_SCRAPER = "apify/web-scraper"  # Free, uses compute credits only
APIFY_CLOUDFLARE_ACTOR = "neatrat/cloudflare-scraper"  # $39/mo, better Cloudflare bypass

# Selectors from Notion Products DB
# Multiple fallback selectors to handle page structure changes
SELECTORS = {
    "price": [
        "#plus > div.flex.w-full.flex-col.justify-between.gap-8 > div.flex.flex-col.gap-4 > div > div > span",
        "#plus span[class*='price']",
        "#plus .price",
        "[data-testid='plus-price']",
        "#plus span:contains('$')",
    ],
    "currency": [
        "#plus > div.flex.w-full.flex-col.justify-between.gap-8 > div.flex.flex-col.gap-4 > div > div > span",
        "#plus span[class*='currency']",
    ],
    "period": [
        "#plus > div.flex.w-full.flex-col.justify-between.gap-8 > div.flex.flex-col.gap-4 > div > div > div",
        "#plus div:contains('/month')",
        "#plus div:contains('/mo')",
    ],
    "plan_name": [
        "#plus > div.flex.w-full.flex-col.justify-between.gap-8 > div:nth-child(1) > div > h3",
        "#plus h3",
        "[data-testid='plus-name']",
    ],
}

URL = "https://chatgpt.com/pricing"
PRODUCT_NAME = "ChatGPT Plus"


def get_geonode_proxy(country_code: str) -> str:
    """
    Build Geonode proxy URL with country targeting.
    
    Format: http://username-country-XX:password@premium-residential.geonode.com:9000
    """
    username = os.getenv("GEONODE_USERNAME")
    password = os.getenv("GEONODE_PASSWORD")
    
    if not username or not password:
        raise ValueError(
            "GEONODE_USERNAME and GEONODE_PASSWORD environment variables are required. "
            "Sign up at https://geonode.com and get credentials from your dashboard."
        )
    
    # Geonode format: username-country-XX
    proxy_username = f"{username}-country-{country_code}"
    proxy_url = f"http://{proxy_username}:{password}@premium-residential.geonode.com:9000"
    
    return proxy_url


def fetch_page_with_apify(url: str, country_code: str) -> Optional[str]:
    """
    Fetch page HTML using Apify's free web-scraper actor.
    Uses compute credits only (no monthly fee).
    Returns HTML or None on failure.
    """
    try:
        from apify_client import ApifyClient
    except ImportError:
        raise ValueError("apify-client not installed. Run: pip install apify-client")
    
    apify_token = os.getenv("APIFY_TOKEN")
    if not apify_token:
        raise ValueError(
            "APIFY_TOKEN environment variable is required. "
            "Get your token from https://console.apify.com/account/integrations"
        )
    
    print(f"  [{country_code}] Fetching via Apify web-scraper (free, compute credits only)...")
    
    try:
        client = ApifyClient(apify_token)
        
        # Use apify/web-scraper with page function to extract HTML
        run_input = {
            "startUrls": [{"url": url}],
            "pageFunction": """
                async function pageFunction(context) {
                    const { page, request } = context;
                    
                    // Wait for page to load
                    await page.waitForTimeout(5000);
                    
                    // Check for Cloudflare challenge
                    const content = await page.content();
                    if (content.includes('Just a moment') || content.includes('challenges.cloudflare.com')) {
                        // Wait longer for challenge to resolve
                        await page.waitForTimeout(15000);
                    }
                    
                    // Try to wait for pricing content
                    try {
                        await page.waitForSelector('#plus, [data-testid="plus-plan"]', { timeout: 10000 });
                    } catch (e) {
                        // Continue anyway
                    }
                    
                    const html = await page.content();
                    return { html, url: request.url };
                }
            """,
            "proxyConfiguration": {"useApifyProxy": True},
            "maxRequestsPerCrawl": 1,
        }
        
        # Call the actor and wait for it to finish
        run = client.actor(APIFY_WEB_SCRAPER).call(run_input=run_input, timeout_secs=180)
        
        # Get results from default dataset
        dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if not dataset_items:
            print(f"  [{country_code}] Apify returned no results")
            return None
        
        result = dataset_items[0]
        html = result.get("html", "")
        
        if not html:
            print(f"  [{country_code}] Apify returned empty content")
            return None
        
        # Check if we got past Cloudflare
        if "Just a moment" in html or "challenges.cloudflare.com" in html:
            print(f"  [{country_code}] Apify got stuck on Cloudflare challenge")
            return None
        
        print(f"  [{country_code}] Apify success")
        return html
        
    except Exception as e:
        print(f"  [{country_code}] Apify error: {e}")
        return None


def fetch_page_with_patchright(url: str, country_code: str, use_proxy: bool = False, visible: bool = False) -> Optional[str]:
    """
    Fetch page HTML using patchright - a patched Playwright that bypasses bot detection.
    This is FREE and very effective against Cloudflare Turnstile.
    
    Args:
        url: The URL to fetch
        country_code: ISO country code for logging (and proxy targeting if use_proxy=True)
        use_proxy: If True, use Geonode proxy for geo-targeting
        visible: If True, run browser in non-headless mode (visible window)
    
    Returns HTML or None on failure.
    """
    mode_desc = []
    if visible:
        mode_desc.append("visible")
    if use_proxy:
        mode_desc.append("proxy")
    mode_str = " + ".join(mode_desc) if mode_desc else "headless"
    print(f"  [{country_code}] Fetching via patchright ({mode_str})...")
    
    try:
        from patchright.sync_api import sync_playwright
    except ImportError:
        raise ValueError(
            "patchright not installed. Run: pip install patchright && patchright install chromium"
        )
    
    # Get proxy config if needed
    proxy_config = None
    if use_proxy:
        proxy_url = get_geonode_proxy(country_code)
        # Parse proxy URL: http://username:password@host:port
        proxy_parts = proxy_url.replace("http://", "").split("@")
        auth = proxy_parts[0].split(":")
        server = proxy_parts[1]
        proxy_config = {
            "server": f"http://{server}",
            "username": auth[0],
            "password": auth[1],
        }
    
    try:
        with sync_playwright() as p:
            # Launch with stealth arguments for maximum anti-detection
            # Use installed Chrome (channel='chrome') for better rendering
            # Non-headless (visible=True) is harder for Cloudflare to detect
            browser = p.chromium.launch(
                headless=not visible,
                channel="chrome",  # Use system Chrome instead of bundled Chromium
                proxy=proxy_config,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                ],
            )
            
            # Create context with realistic browser settings
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York",
            )
            page = context.new_page()
            
            # Navigate to page (domcontentloaded is faster than networkidle)
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for Cloudflare challenge to pass (if present)
            # In visible mode, try to click the Turnstile checkbox if it appears
            max_wait = 90 if visible else 60
            waited = 0
            clicked_turnstile = False
            
            while waited < max_wait:
                title = page.title()
                html = page.content()
                
                is_cloudflare = (
                    "Just a moment" in title or
                    "Just a moment" in html or
                    "challenges.cloudflare.com" in html or
                    "cf-turnstile" in html
                )
                
                if is_cloudflare:
                    # Try to click the Turnstile checkbox if visible mode
                    if visible and not clicked_turnstile:
                        try:
                            # Turnstile checkbox is in an iframe from challenges.cloudflare.com
                            for frame in page.frames:
                                if "challenges.cloudflare.com" in frame.url or "turnstile" in frame.url:
                                    # Multiple selectors to try
                                    selectors = [
                                        "input[type='checkbox']",
                                        "#cf-turnstile-response",
                                        ".cf-turnstile",
                                        "body",  # Sometimes clicking anywhere in the iframe works
                                    ]
                                    for sel in selectors:
                                        try:
                                            el = frame.query_selector(sel)
                                            if el:
                                                el.click()
                                                print(f"  [{country_code}] Clicked Turnstile ({sel})")
                                                clicked_turnstile = True
                                                break
                                        except:
                                            continue
                                    if clicked_turnstile:
                                        break
                            
                            # Also try clicking directly on the page where the widget appears
                            if not clicked_turnstile:
                                turnstile_widget = page.query_selector("[data-turnstile-widget], .cf-turnstile, iframe[src*='challenges.cloudflare']")
                                if turnstile_widget:
                                    # Click in the center of the widget
                                    box = turnstile_widget.bounding_box()
                                    if box:
                                        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                                        print(f"  [{country_code}] Clicked Turnstile widget area")
                                        clicked_turnstile = True
                        except Exception as e:
                            pass  # Checkbox not ready yet, will retry
                    
                    if waited % 10 == 0:  # Print less frequently
                        print(f"  [{country_code}] Waiting for Cloudflare challenge... ({waited}s)")
                    time.sleep(2)
                    waited += 2
                else:
                    if waited > 0:
                        print(f"  [{country_code}] Cloudflare passed after {waited}s")
                    break
            
            if waited >= max_wait:
                print(f"  [{country_code}] Cloudflare challenge did not pass after {max_wait}s")
                browser.close()
                return None
            
            # Wait for pricing section to appear
            pricing_found = False
            for selector in ["#plus", "[data-testid='plus-plan']", "h3:has-text('Plus')"]:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    print(f"  [{country_code}] Found pricing section")
                    pricing_found = True
                    break
                except Exception:
                    continue
            
            if not pricing_found:
                print(f"  [{country_code}] Warning: pricing section not found, continuing...")
            
            # Wait for price VALUE to appear (JS hydration)
            # Use wait_for_function for efficient, event-driven waiting
            # This is much faster than polling - it reacts immediately when price loads
            import re
            
            try:
                # JavaScript function that returns the price text when it appears
                # Checks if #plus section contains a number followed by "/ month"
                price_js = """
                    () => {
                        const plus = document.querySelector('#plus');
                        if (!plus) return null;
                        const text = plus.innerText;
                        // Match: currency symbol + number + / month
                        const match = text.match(/[\\$€£₹₽R]?\\s*[\\d,]+(?:\\.\\d+)?\\s*\\/\\s*month/i);
                        return match ? match[0] : null;
                    }
                """
                price_text = page.wait_for_function(price_js, timeout=60000)
                rendered_price = price_text.json_value()
                print(f"  [{country_code}] Price rendered: {rendered_price}")
            except Exception as e:
                print(f"  [{country_code}] Warning: price wait timed out - {e}")
            
            # Final wait for any remaining JS rendering
            time.sleep(1)
            html = page.content()
            browser.close()
            
            return html
            
    except Exception as e:
        print(f"  [{country_code}] patchright error: {e}")
        return None


def fetch_page_with_crawlee(url: str, country_code: str) -> Optional[str]:
    """
    Fetch page HTML using Crawlee's PlaywrightCrawler with anti-detection.
    This is FREE and has better fingerprinting than plain playwright-stealth.
    Returns HTML or None on failure.
    """
    import asyncio
    
    print(f"  [{country_code}] Fetching via Crawlee (free, anti-detection)...")
    
    result_html = None
    
    async def crawl():
        nonlocal result_html
        try:
            from crawlee.crawlers import PlaywrightCrawler
            from crawlee import ConcurrencySettings
            
            crawler = PlaywrightCrawler(
                max_requests_per_crawl=1,
                headless=True,
                browser_type='chromium',
                concurrency_settings=ConcurrencySettings(max_concurrency=1),
                # Don't block on 403 (Cloudflare challenge)
                session_pool_options={'blocked_status_codes': []},
            )
            
            @crawler.router.default_handler
            async def request_handler(context):
                nonlocal result_html
                page = context.page
                
                # Wait for Cloudflare challenge to pass
                max_wait = 30
                waited = 0
                while waited < max_wait:
                    html = await page.content()
                    if "Just a moment" in html or "challenges.cloudflare.com" in html:
                        print(f"  [{country_code}] Waiting for Cloudflare... ({waited}s)")
                        await asyncio.sleep(2)
                        waited += 2
                    else:
                        break
                
                if waited >= max_wait:
                    print(f"  [{country_code}] Cloudflare challenge did not pass after {max_wait}s")
                
                # Try to find pricing content
                try:
                    await page.wait_for_selector('#plus, [data-testid="plus-plan"], h3:has-text("Plus")', timeout=15000)
                    print(f"  [{country_code}] Found pricing content")
                except Exception:
                    print(f"  [{country_code}] Warning: Pricing selector not found")
                
                await asyncio.sleep(2)  # Let page fully render
                result_html = await page.content()
            
            await crawler.run([url])
            
        except Exception as e:
            print(f"  [{country_code}] Crawlee error: {e}")
    
    # Run the async crawler
    asyncio.run(crawl())
    
    return result_html


def fetch_page_with_nodriver(url: str, country_code: str) -> Optional[str]:
    """
    Fetch page HTML using undetected-chromedriver.
    Patches ChromeDriver to avoid bot detection.
    FREE and often bypasses Cloudflare.
    Returns HTML or None on failure.
    """
    print(f"  [{country_code}] Fetching via undetected-chromedriver...")
    
    try:
        import undetected_chromedriver as uc
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Configure options
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")  # New headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # Launch browser
        driver = uc.Chrome(options=options, use_subprocess=True)
        
        try:
            # Navigate to URL
            driver.get(url)
            
            # Wait for Cloudflare challenge to pass
            max_wait = 30
            waited = 0
            while waited < max_wait:
                html = driver.page_source
                if "Just a moment" in html or "challenges.cloudflare.com" in html:
                    print(f"  [{country_code}] Waiting for Cloudflare... ({waited}s)")
                    time.sleep(2)
                    waited += 2
                else:
                    break
            
            if waited >= max_wait:
                print(f"  [{country_code}] Cloudflare challenge did not pass after {max_wait}s")
            else:
                print(f"  [{country_code}] Cloudflare passed!")
            
            # Wait for pricing content
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#plus, [data-testid='plus-plan']"))
                )
                print(f"  [{country_code}] Found pricing section")
            except Exception:
                print(f"  [{country_code}] Warning: pricing selector not found, continuing...")
            
            # Let page fully render
            time.sleep(2)
            
            html = driver.page_source
            return html
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"  [{country_code}] undetected-chromedriver error: {e}")
        return None


def fetch_page_with_proxy(url: str, country_code: str, country_name: str) -> Optional[str]:
    """
    Fetch page HTML using Playwright with Geonode proxy for given country.
    Uses stealth mode to bypass Cloudflare and bot detection.
    Returns HTML or None on failure.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ValueError(
            "Playwright is not installed. Run: pip install playwright && playwright install chromium"
        )
    
    # playwright-stealth v2 uses different API
    stealth_context_manager = None
    try:
        from playwright_stealth import Stealth
        stealth_context_manager = Stealth
    except ImportError:
        try:
            # Fallback for older versions
            from playwright_stealth import stealth_sync
            stealth_context_manager = stealth_sync
        except ImportError:
            print(f"  [{country_code}] Warning: playwright-stealth not installed, bot detection may occur")
    
    proxy_url = get_geonode_proxy(country_code)
    
    # Parse proxy URL
    # Format: http://username:password@host:port
    proxy_parts = proxy_url.replace("http://", "").split("@")
    auth = proxy_parts[0].split(":")
    server = proxy_parts[1].split(":")
    
    proxy_config = {
        "server": f"http://{server[0]}:{server[1]}",
        "username": auth[0],
        "password": auth[1],
    }
    
    # Check if we should run non-headless for debugging
    headless = os.getenv("SCRAPER_HEADLESS", "1") != "0"
    if not headless:
        print(f"  [{country_code}] Running in non-headless mode (browser visible)...")
    else:
        print(f"  [{country_code}] Fetching via Geonode proxy (stealth mode)...")
    
    try:
        with sync_playwright() as p:
            # Launch with stealth-friendly options
            browser = p.chromium.launch(
                headless=headless,
                proxy=proxy_config,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/New_York",
            )
            
            page = context.new_page()
            
            # Apply stealth to avoid bot detection (playwright-stealth v2 API)
            if stealth_context_manager:
                try:
                    stealth = stealth_context_manager()
                    stealth.apply_stealth_sync(page)
                    print(f"  [{country_code}] Applied playwright-stealth")
                except Exception as e:
                    print(f"  [{country_code}] Stealth apply failed: {e}")
            
            # Navigate and wait for network to settle
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wait for Cloudflare challenge to pass (if present)
            # Cloudflare challenges typically complete within 5-10 seconds
            max_cf_wait = 30  # seconds
            cf_wait_interval = 2
            waited = 0
            while waited < max_cf_wait:
                html = page.content()
                # Check if still on Cloudflare challenge page
                if "Just a moment" in html or "challenges.cloudflare.com" in html:
                    print(f"  [{country_code}] Waiting for Cloudflare challenge... ({waited}s)")
                    time.sleep(cf_wait_interval)
                    waited += cf_wait_interval
                else:
                    break
            
            if waited >= max_cf_wait:
                print(f"  [{country_code}] Cloudflare challenge did not complete after {max_cf_wait}s")
            
            # Wait for actual pricing content to appear
            # Try multiple possible selectors for the Plus plan
            pricing_selectors = [
                "#plus",
                "[data-testid='plus-plan']",
                "text=Plus",
                "h3:has-text('Plus')",
            ]
            
            found_pricing = False
            for selector in pricing_selectors:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    print(f"  [{country_code}] Found pricing content via: {selector}")
                    found_pricing = True
                    break
                except Exception:
                    continue
            
            if not found_pricing:
                print(f"  [{country_code}] Warning: Could not find pricing selectors, page may not have loaded correctly")
            
            # Let page fully render
            time.sleep(2)
            
            html = page.content()
            browser.close()
            
            return html
            
    except Exception as e:
        print(f"  [{country_code}] Error fetching page: {e}")
        return None


def extract_text(soup: BeautifulSoup, selectors) -> str:
    """Extract text from first element matching any of the selectors."""
    if not selectors:
        return ""
    
    # Handle both single selector string and list of selectors
    selector_list = selectors if isinstance(selectors, list) else [selectors]
    
    for selector in selector_list:
        try:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text:
                    return text
        except Exception:
            continue
    return ""


def extract_price_from_html(soup: BeautifulSoup, plus_section) -> Optional[str]:
    """
    Try multiple strategies to extract price from the Plus plan section.
    Returns raw price string or None.
    """
    import re
    
    if not plus_section:
        return None
    
    # Look for common price patterns in the section text
    text = plus_section.get_text()
    
    # Pattern: $20/mo, $20 /month, 20,00€/month, ZAR 399, etc
    price_patterns = [
        r"(\$[\d,]+(?:\.\d{2})?)",  # $20 or $20.00
        r"([\d,]+(?:\.\d{2})?\s*(?:€|£|₹|¥|₽))",  # 20€ or 20.00 €
        r"(€\s*[\d,]+(?:\.\d{2})?)",  # €20
        r"(£\s*[\d,]+(?:\.\d{2})?)",  # £20
        r"(₹\s*[\d,]+)",  # ₹2000
        r"(R\$\s*[\d,]+(?:\.\d{2})?)",  # R$100 (Brazilian Real)
        r"([A-Z]{3}\s+[\d,]+(?:\.\d{2})?)",  # ZAR 399, USD 20 (currency code + amount)
        r"([\d,]+(?:\.\d{2})?)\s*/\s*month",  # 399 / month (number before /month)
    ]
    
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    
    return None


def parse_price(raw: str) -> Optional[float]:
    """Parse price string to float. Handles $19.99, 19,99 €, ZAR 399, R$99.90, etc."""
    if not raw or not isinstance(raw, str):
        return None
    
    import re
    # Remove currency symbols (including R$ for Brazilian Real)
    cleaned = re.sub(r"R\$", "", raw)  # Brazilian Real first (before removing $)
    cleaned = re.sub(r"[$€£¥₹₽₪₩¢]", "", cleaned)
    cleaned = re.sub(r"\b(USD|EUR|GBP|CAD|AUD|INR|BRL|JPY|MXN|ARS|TRY|PLN|ZAR|NGN|PHP|IDR|THB|Rp)\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[\s]", "", cleaned)  # Remove spaces but not commas/dots yet
    
    # Handle thousand separators vs decimal separators
    # European: 1.234,56 or 1 234,56 -> 1234.56
    # US/UK: 1,234.56 -> 1234.56
    if re.search(r"\d+,\d{2}$", cleaned):  # Ends with ,XX (European decimal)
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:  # US format or no decimal
        cleaned = cleaned.replace(",", "")  # Remove thousand separators
    
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_currency(raw: str) -> str:
    """Extract currency from price string."""
    import re
    if not raw:
        return "USD"
    
    # First check for explicit currency codes (ZAR 399, USD 20, etc.)
    code_match = re.match(r"([A-Z]{3})\s+[\d,]+", raw)
    if code_match:
        return code_match.group(1)
    
    # Common currency symbols and codes
    # Check R$ (Brazilian Real) BEFORE checking for just $
    if "R$" in raw:
        return "BRL"
    if "$" in raw:
        if "CAD" in raw or "AUD" in raw or "MXN" in raw or "ARS" in raw:
            if "CAD" in raw:
                return "CAD"
            if "AUD" in raw:
                return "AUD"
            if "MXN" in raw:
                return "MXN"
            if "ARS" in raw:
                return "ARS"
        return "USD"
    elif "€" in raw or "EUR" in raw:
        return "EUR"
    elif "£" in raw or "GBP" in raw:
        return "GBP"
    elif "₹" in raw or "INR" in raw:
        return "INR"
    elif "BRL" in raw:
        return "BRL"
    elif "¥" in raw or "JPY" in raw:
        return "JPY"
    elif "₺" in raw or "TRY" in raw:
        return "TRY"
    elif "zł" in raw or "PLN" in raw:
        return "PLN"
    elif "ZAR" in raw:
        return "ZAR"
    elif "₦" in raw or "NGN" in raw:
        return "NGN"
    elif "₱" in raw or "PHP" in raw:
        return "PHP"
    elif "Rp" in raw or "IDR" in raw:
        return "IDR"
    elif "฿" in raw or "THB" in raw:
        return "THB"
    
    return "USD"


def scrape_region(country_code: str, country_name: str, debug_html: bool = False, mode: str = "patchright", use_proxy: bool = False, visible: bool = False) -> bool:
    """
    Scrape ChatGPT Plus pricing for a single region.
    Returns True if successful, False otherwise.
    
    Args:
        country_code: ISO country code (e.g., "US")
        country_name: Human-readable country name
        debug_html: If True, save fetched HTML to debug files
        mode: "patchright" (free, default), "crawlee" (free), "apify" (paid), or "direct" (proxy)
        use_proxy: If True and mode is "patchright", use Geonode proxy for geo-targeting
        visible: If True and mode is "patchright", run browser visibly (non-headless)
    """
    print(f"\n[{country_code}] Scraping {country_name}...")
    
    # Fetch page based on mode
    if mode == "patchright":
        html = fetch_page_with_patchright(URL, country_code, use_proxy=use_proxy, visible=visible)
    elif mode == "nodriver":
        html = fetch_page_with_nodriver(URL, country_code)
    elif mode == "crawlee":
        html = fetch_page_with_crawlee(URL, country_code)
    elif mode == "apify":
        html = fetch_page_with_apify(URL, country_code)
    else:  # direct
        html = fetch_page_with_proxy(URL, country_code, country_name)
    
    if not html:
        print(f"  [{country_code}] Failed to fetch page")
        return False
    
    # Debug: save HTML for inspection
    if debug_html:
        debug_path = Path(__file__).parent / "data" / f"debug_{country_code}.html"
        debug_path.parent.mkdir(exist_ok=True)
        debug_path.write_text(html, encoding="utf-8")
        print(f"  [{country_code}] Saved debug HTML to {debug_path}")
    
    # Parse HTML
    soup = BeautifulSoup(html, "lxml")
    
    # Try to find the Plus section first
    plus_section = None
    plus_selectors = ["#plus", "[data-testid='plus-plan']", ".plus-plan"]
    for sel in plus_selectors:
        plus_section = soup.select_one(sel)
        if plus_section:
            break
    
    # Also try finding by text content
    if not plus_section:
        for h3 in soup.find_all("h3"):
            if "Plus" in h3.get_text():
                plus_section = h3.find_parent("div")
                break
    
    # Extract data using selectors
    price_raw = extract_text(soup, SELECTORS["price"])
    
    # If selector-based extraction failed, try pattern-based extraction
    if not price_raw and plus_section:
        price_raw = extract_price_from_html(soup, plus_section)
        if price_raw:
            print(f"  [{country_code}] Found price via pattern matching: {price_raw}")
    
    currency_raw = extract_text(soup, SELECTORS["currency"])
    period_raw = extract_text(soup, SELECTORS["period"])
    plan_name_raw = extract_text(soup, SELECTORS["plan_name"])
    
    # Parse price
    amount = parse_price(price_raw)
    if amount is None:
        # Additional debug info
        if plus_section:
            print(f"  [{country_code}] Plus section found but couldn't extract price")
            print(f"  [{country_code}] Plus section text preview: {plus_section.get_text()[:200]}...")
        else:
            print(f"  [{country_code}] Plus section NOT found")
            # Check for common error pages
            page_text = soup.get_text().lower()
            if "just a moment" in page_text or "cloudflare" in page_text:
                print(f"  [{country_code}] Cloudflare challenge page detected!")
            elif "access denied" in page_text:
                print(f"  [{country_code}] Access denied page detected!")
        print(f"  [{country_code}] Failed to parse price from: '{price_raw}'")
        return False
    
    # Extract currency
    currency = extract_currency(price_raw or currency_raw)
    
    # Clean up period - normalize various formats to standard names
    period = (period_raw or "").strip()
    period_lower = period.lower()
    if not period or "month" in period_lower or "/mo" in period_lower:
        period = "Monthly"
    elif "year" in period_lower or "annual" in period_lower:
        period = "Annual"
    elif "week" in period_lower:
        period = "Weekly"
    
    # Plan name
    plan_name = (plan_name_raw or "").strip() or "Plus"
    
    print(f"  [{country_code}] Found: {amount} {currency} / {period} ({plan_name})")
    
    # Push to Notion Scraped Pricing DB
    try:
        code_to_page_id, alias_to_page_id = ensure_regions_cache()
        region_page_id = resolve_region_page_id(country_code, code_to_page_id, alias_to_page_id)
        if not region_page_id:
            raise ValueError(f"Could not resolve region '{country_code}' to Regions DB page id")
        push_price_data(
            product_name=PRODUCT_NAME,
            amount=amount,
            currency=currency,
            period=period,
            plan_name=plan_name,
            source_url=URL,
            success=True,
            region_page_id=region_page_id,
        )
        print(f"  [{country_code}] ✓ Pushed to Scraped Pricing DB")
        return True
    except Exception as e:
        print(f"  [{country_code}] Error pushing to Notion: {e}")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="ChatGPT Plus Multi-Region Scraper")
    parser.add_argument("--country", "-c", help="Scrape only a specific country code (e.g., US, GB)")
    parser.add_argument("--debug", "-d", action="store_true", help="Save HTML to debug files")
    parser.add_argument("--patchright", action="store_true", 
                        help="Use patchright (FREE, stealth anti-detection - default)")
    parser.add_argument("--nodriver", action="store_true", 
                        help="Use nodriver (CDP-based, free anti-detection)")
    parser.add_argument("--crawlee", action="store_true", 
                        help="Use Crawlee (free, Playwright-based)")
    parser.add_argument("--apify", action="store_true", 
                        help="Use Apify's web scraper (costs compute credits)")
    parser.add_argument("--direct", action="store_true", 
                        help="Use direct Playwright+proxy (may be blocked by Cloudflare)")
    parser.add_argument("--proxy", action="store_true",
                        help="Use Geonode proxy with patchright for geo-targeting (requires GEONODE credentials)")
    parser.add_argument("--visible", action="store_true",
                        help="Run browser visibly (non-headless) - harder for Cloudflare to detect")
    args = parser.parse_args()
    
    # Determine mode: patchright (default/free), nodriver, crawlee, apify, or direct (proxy)
    if args.patchright:
        mode = "patchright"
    elif args.nodriver:
        mode = "nodriver"
    elif args.crawlee:
        mode = "crawlee"
    elif args.apify:
        mode = "apify"
    elif args.direct:
        mode = "direct"
    else:
        mode = "patchright"  # Default - best free anti-detection option
    
    print(f"ChatGPT Plus Multi-Region Scraper")
    print(f"=================================")
    print(f"Target: {URL}")
    mode_labels = {
        "patchright": "patchright (FREE, stealth Playwright - best option)",
        "nodriver": "nodriver (FREE, CDP anti-detection)",
        "crawlee": "Crawlee (FREE, Playwright anti-detection)",
        "apify": "Apify (compute credits)",
        "direct": "Direct (Playwright + Geonode proxy)",
    }
    print(f"Mode: {mode_labels[mode]}")
    
    # Check credentials based on mode
    if mode == "apify":
        if not os.getenv("APIFY_TOKEN"):
            print("ERROR: Missing Apify token.")
            print("1. Sign up at https://apify.com")
            print("2. Get your token from https://console.apify.com/account/integrations")
            print("3. Add to .env:")
            print("   APIFY_TOKEN=your_token")
            return 1
    elif mode == "direct" or args.proxy:
        if not os.getenv("GEONODE_USERNAME") or not os.getenv("GEONODE_PASSWORD"):
            print("ERROR: Missing Geonode credentials.")
            print("1. Sign up at https://geonode.com")
            print("2. Add to .env:")
            print("   GEONODE_USERNAME=your_username")
            print("   GEONODE_PASSWORD=your_password")
            return 1
    
    if not os.getenv("NOTION_TOKEN") or not os.getenv("NOTION_SCRAPED_PRICING_DB_ID"):
        print("ERROR: Missing Notion credentials.")
        print("Check .env for NOTION_TOKEN and NOTION_SCRAPED_PRICING_DB_ID")
        return 1
    
    # Fetch regions from Notion Regions DB
    print("Fetching regions from Notion...")
    all_regions = fetch_all_regions()
    if not all_regions:
        print("ERROR: Could not fetch regions from Notion Regions DB.")
        print("Check NOTION_REGIONS_DB_ID in .env and ensure the database is accessible.")
        return 1
    print(f"Found {len(all_regions)} regions in Notion Regions DB")
    
    # Determine regions to scrape
    if args.country:
        # Find the country in fetched regions
        target_regions = [(code, name) for code, name in all_regions if code.upper() == args.country.upper()]
        if not target_regions:
            # Allow arbitrary country code even if not in the DB
            target_regions = [(args.country.upper(), args.country.upper())]
        print(f"Regions to scrape: {len(target_regions)} (filtered)")
    else:
        target_regions = all_regions
        print(f"Regions to scrape: {len(target_regions)}")
    
    # Note: patchright, nodriver, Crawlee, and Apify don't support geo-targeting out of the box
    # For region-specific pricing, use --proxy flag with patchright (recommended)
    # or use --direct mode (may be blocked by Cloudflare)
    if mode in ("patchright", "nodriver", "crawlee", "apify") and len(target_regions) > 1 and not args.proxy:
        print(f"\nNote: {mode} mode scrapes from default location (your IP).")
        print("For region-specific pricing, use --proxy --visible flags.")
        print()
    
    print()
    
    if args.debug:
        print("DEBUG MODE: HTML will be saved to scrapers/data/debug_<CC>.html")
        print()
    
    # Scrape each region
    success_count = 0
    failed_count = 0
    
    for country_code, country_name in target_regions:
        try:
            success = scrape_region(country_code, country_name, debug_html=args.debug, mode=mode, use_proxy=args.proxy, visible=args.visible)
            if success:
                success_count += 1
            else:
                failed_count += 1
            
            # Rate limiting - wait between requests (skip if single country)
            if len(target_regions) > 1:
                time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            break
        except Exception as e:
            print(f"  [{country_code}] Unexpected error: {e}")
            failed_count += 1
    
    print(f"\n{'='*50}")
    print(f"Done! Success: {success_count}, Failed: {failed_count}")
    print(f"{'='*50}")
    
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
