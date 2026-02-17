from rxconfig import config
import reflex as rx
import json
import os

docs_url = "https://reflex.dev/docs/getting-started/introduction"
filename = f"{config.app_name}/{config.app_name}.py"

# CMS pages loader (reads myapp/data/cms_pages.json)
CMS_PAGES_PATH = os.path.join(os.path.dirname(__file__), "data", "cms_pages.json")

def load_cms_pages():
    """Load CMS pages JSON (array of rows) -> Python list[dict]"""
    try:
        with open(CMS_PAGES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print("cms_pages.json did not contain a JSON array; using empty list")
            return []
        return data
    except Exception as e:
        print(f"Error loading cms_pages.json: {e}")
        return []

def deduplicate_cms_rows(rows: list[dict]) -> list[dict]:
    """Keep only the most recent row per (Product, Region) pair,
    based on the 'Last Price Update' ISO timestamp."""
    best: dict[tuple, dict] = {}
    for row in rows:
        key = (
            (row.get("Product") or "").strip(),
            (row.get("Region") or "").strip(),
        )
        existing = best.get(key)
        if existing is None or (row.get("Last Price Update") or "") > (existing.get("Last Price Update") or ""):
            best[key] = row
    return list(best.values())

# Make rows available to myapp.py for routing
cms_rows: list[dict] = deduplicate_cms_rows(load_cms_pages())

# Derive pricing table data directly from CMS rows (exported by n8n)
def derive_pricing_from_cms(rows: list[dict], product_filter: str | None = None) -> list[dict]:
    items: list[dict] = []
    for row in rows:
        if product_filter and (row.get("Product") or "").strip() != product_filter:
            continue
        region = (row.get("Region") or "").strip()
        amount = row.get("Latest Price ($)")
        period = (row.get("Period") or "/mo").strip()

        if not region or amount is None:
            continue

        try:
            amt = float(amount)
        except (TypeError, ValueError):
            continue

        items.append(
            {
                "region_name": region,
                "amount": amt,
                "price_display": f"${amt:.2f} {period}",
                "slug": (row.get("Slug") or "").strip(),
            }
        )

    # Sort by amount (cheapest first) and take top 10
    items.sort(key=lambda x: x["amount"])
    return items[:10]

PRICING_DATA: list[dict] = derive_pricing_from_cms(cms_rows)

# Per-product pricing data for product pages
PRODUCTS = {(row.get("Product") or "").strip() for row in cms_rows if row.get("Product")}
PRICING_DATA_BY_PRODUCT: dict[str, list[dict]] = {
    product: derive_pricing_from_cms(cms_rows, product_filter=product)
    for product in PRODUCTS
}

# Tools config for homepage pills (derived from CMS products)
TOOLS_CONFIG = []
for product in sorted(PRODUCTS):
    product_pricing = PRICING_DATA_BY_PRODUCT.get(product, [])
    if product_pricing:
        cheapest_slug = product_pricing[0].get("slug", "")
        TOOLS_CONFIG.append({
            "name": product,
            "href": f"/{cheapest_slug}" if cheapest_slug else "#",
        })

# Helper function to get unique countries/regions from CMS data
def get_unique_regions(rows: list[dict]) -> list[dict]:
    """Extract unique regions with slugs from CMS rows"""
    seen = set()
    regions = []
    for row in rows:
        region = (row.get("Region") or "").strip()
        slug = (row.get("Slug") or "").strip()
        if region and slug and region not in seen:
            seen.add(region)
            regions.append({
                "name": region,
                "slug": slug,
            })
    return sorted(regions, key=lambda x: x["name"])

# Get unique regions for country list
UNIQUE_REGIONS = get_unique_regions(cms_rows)

# FAQ content data structure
FAQ_ITEMS = [
    {
        "question": "Is it legal to buy software using another country's price?",
        "answer": (
            "Short answer: it depends on the company's terms, not on PriceDuck.\n"
            "Most pricing rules live in the vendor's terms of service. Lots of people use regional pricing, "
            "but it can still break the rules for a specific product. Read the official terms before you decide "
            "— nothing here is legal advice."
        ),
    },
    {
        "question": "Can the company tell I'm using a VPN or a different region?",
        "answer": (
            "Sometimes, yes.\n"
            "Companies can look at things like your IP address, billing country, and the country on your account. "
            "If those don't match, they might ask for extra checks, block the purchase, or cancel a subscription. "
            "It's annoying, not criminal, but it's a risk you should know about."
        ),
    },
    {
        "question": "Which payment methods usually work for regional pricing?",
        "answer": (
            "The most reliable options are usually local or region-friendly cards.\n"
            "That can mean a local bank card, a multi-currency card (like Wise, Revolut, etc.), or sometimes PayPal. "
            "What works changes by product and country. PriceDuck doesn't process payments and can't guarantee any specific method will be accepted."
        ),
    },
    {
        "question": "What billing country should I use?",
        "answer": (
            "In most cases, the billing country should match the store region and/or the card's country.\n"
            "Putting completely fake details can violate a product's terms of service. Some people still do it, "
            "but you should assume the company can ask for proof or push back later."
        ),
    },
    {
        "question": "Can my account get banned for using regional pricing?",
        "answer": (
            "Vendors can enforce their rules in different ways.\n"
            "In practice, the most common outcomes are: failed payments, requests for extra verification, or losing access to the cheaper offer. "
            "Permanent bans are possible but not typical. If you're worried about that risk, stick to your home region."
        ),
    },
    {
        "question": "Does PriceDuck sell VPNs or subscriptions?",
        "answer": (
            "No. PriceDuck only shows you where prices are different.\n"
            "We don't run a VPN, we don't resell software, and we don't sit in the middle of your payments. "
            "Some links might be affiliate links, and if that's the case we'll say so."
        ),
    },
    {
        "question": "Why are prices so different between countries in the first place?",
        "answer": (
            "Companies set prices by region based on things like income levels, local competition, and taxes.\n"
            "The product is the same, but the \"fair\" price can look very different from one country to another. "
            "PriceDuck's job is just to make those differences easy to see."
        ),
    },
]

# FAQ section component
def faq_section() -> rx.Component:
    """Return an FAQ section matching homepage pattern"""
    from .design_constants import (
        HEADING_LG_STYLE, HEADING_MD_STYLE, BODY_TEXT_STYLE,
        COLOR_TEXT_SECONDARY, COLOR_BORDER, COLOR_BACKGROUND_ALT,
        MAX_WIDTH, PADDING_SECTION, SPACING_SM, SPACING_XL, SPACING_2XL,
    )

    return rx.box(
        rx.box(
            rx.heading("FAQ", as_="h2", margin_bottom=SPACING_2XL, **HEADING_LG_STYLE),
            *[
                rx.box(
                    rx.heading(
                        item["question"],
                        as_="h3",
                        margin_bottom=SPACING_SM,
                        **HEADING_MD_STYLE,
                    ),
                    rx.text(
                        item["answer"],
                        color=COLOR_TEXT_SECONDARY,
                        white_space="pre-line",
                        **BODY_TEXT_STYLE,
                    ),
                    border_top=f"1px solid {COLOR_BORDER}" if i > 0 else "none",
                    padding_top=SPACING_XL if i > 0 else "0",
                    margin_bottom=SPACING_XL,
                )
                for i, item in enumerate(FAQ_ITEMS)
            ],
            max_width=MAX_WIDTH,
            margin="0 auto",
            padding=PADDING_SECTION,
        ),
        background=COLOR_BACKGROUND_ALT,
    )

# JSON-LD FAQPage schema generator
def faq_json_ld() -> rx.Component:
    """Generate JSON-LD FAQPage schema from FAQ_ITEMS"""
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["answer"],
                },
            }
            for item in FAQ_ITEMS
        ],
    }
    
    # Use rx.html to render raw HTML script tag with JSON-LD
    json_str = json.dumps(schema, indent=2, ensure_ascii=False)
    script_html = f'<script type="application/ld+json">{json_str}</script>'
    
    return rx.html(script_html)

# Page factory
def make_cms_page(row: dict):
    """Return a Reflex page function"""
    title = row.get("Page Title", "Untitled")
    intro = row.get("Intro Paragraph", "No introduction")
    price_info = row.get("Price Info", "No price info")
    faq = row.get("FAQ", "No FAQ")
    meta_title = row.get("SEO Meta Title", "Untitled")
    meta_description = row.get("SEO Meta Description", "No description")
    useful_extras = row.get("Useful Extras", "No useful extras")
    latest_price_dollar = row.get("Latest Price ($)", "No latest price")
    latest_price_currency = row.get("Latest Price Currency", "No latest price currency")
    latest_price_period = row.get("Period", "No latest price period")
    last_price_update = row.get("Last Price Update - Human", "No last price update")
    all_pricing_rows = row.get("All Pricing Rows", "No all pricing rows")
    latest_pricing_row = row.get("Latest Pricing Row", "No latest pricing row")
    page_id = row.get("Page ID", "No page ID")
    canonical_path = row.get("Canonical Path", "No canonical path")
    region_name = row.get("Region", "No region name")
    latest_price_display = f"${latest_price_dollar:.2f}"

    # Shared variables for page content (used across sections)
    product_name = ((row.get("Product") or title) or "This product").strip()

    product_pricing = PRICING_DATA_BY_PRODUCT.get(product_name, PRICING_DATA)
    cheapest_entry = product_pricing[0] if product_pricing else None
    if cheapest_entry:
        cheapest_region_name = cheapest_entry["region_name"]
        cheapest_region_price_display = f"${cheapest_entry['amount']:.2f}"
    else:
        cheapest_region_name = "Loading..."
        cheapest_region_price_display = "Loading..."

    vpn_affiliate_link = "https://go.nordvpn.net/aff_c?offer_id=15&aff_id=120959&url_id=902"
    how_to_heading = (
        f"How to access {cheapest_region_name} pricing"
        if cheapest_region_name != "Loading..."
        else "How to access the lowest Creative Cloud pricing"
    )

    def page() -> rx.Component:
        from .design_constants import (
            MAX_WIDTH, COLOR_TEXT_MUTED,
            HEADING_LG_STYLE, HEADING_MD_STYLE, BODY_TEXT_STYLE,
            BUTTON_STYLE, LINK_STYLE, STEP_NUMBER_STYLE, CALLOUT_BOX_STYLE,
            COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BACKGROUND_ALT, COLOR_BLACK,
            PADDING_SECTION, FONT_SIZE_SM, FONT_SIZE_BASE,
            SPACING_XS, SPACING_SM, SPACING_MD, SPACING_LG, SPACING_XL, SPACING_2XL,
        )
        from .components import site_header, site_footer

        return rx.fragment(
            # JSON-LD FAQPage schema
            faq_json_ld(),

            # Header
            site_header(),

            # Hero section
            rx.box(
                rx.heading(title, as_="h1", margin_bottom=SPACING_MD, **HEADING_LG_STYLE),
                rx.text(intro, **BODY_TEXT_STYLE, color=COLOR_TEXT_SECONDARY),
                max_width=MAX_WIDTH,
                margin="0 auto",
                padding=PADDING_SECTION,
            ),

            # Main content - price callouts and table
            rx.box(
                rx.vstack(
                    # Latest price callout
                    rx.box(
                        rx.vstack(
                            rx.text("Latest Price", font_size=FONT_SIZE_SM, font_weight="700", color=COLOR_TEXT_SECONDARY, margin_bottom=SPACING_XS),
                            rx.heading(region_name, as_="h2", margin_bottom=SPACING_XS, **HEADING_MD_STYLE),
                            rx.heading(latest_price_display, as_="h1", margin_bottom=SPACING_XS, **HEADING_LG_STYLE),
                            rx.text("per month", font_size=FONT_SIZE_SM, color=COLOR_TEXT_SECONDARY),
                            rx.text(f"Last updated {last_price_update}", font_size=FONT_SIZE_SM, color=COLOR_TEXT_MUTED, margin_top=SPACING_XS),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        **CALLOUT_BOX_STYLE,
                    ),

                    # Cheapest price callout
                    rx.box(
                        rx.vstack(
                            rx.text("Cheapest Price", font_size=FONT_SIZE_SM, font_weight="700", color=COLOR_TEXT_SECONDARY, margin_bottom=SPACING_XS),
                            rx.heading(cheapest_region_name, as_="h2", margin_bottom=SPACING_XS, **HEADING_MD_STYLE),
                            rx.heading(cheapest_region_price_display, as_="h1", margin_bottom=SPACING_XS, **HEADING_LG_STYLE),
                            rx.text("per month", font_size=FONT_SIZE_SM, color=COLOR_TEXT_SECONDARY, margin_bottom=SPACING_MD),
                            rx.link(
                                rx.box(
                                    "Unlock This Price with NordVPN",
                                    **BUTTON_STYLE,
                                ),
                                href="https://go.nordvpn.net/aff_c?offer_id=15&aff_id=120959&url_id=902",
                                is_external=True,
                                text_decoration="none",
                            ),
                            spacing="1",
                            align="start",
                            width="100%",
                        ),
                        **CALLOUT_BOX_STYLE,
                    ),

                    # Table callout card
                    rx.box(
                        rx.vstack(
                            rx.heading(f"Top 10 cheapest countries for {product_name}", as_="h2", margin_bottom=SPACING_XL, **HEADING_LG_STYLE),
                            pricing_table(product_pricing),
                            align="start",
                            width="100%",
                        ),
                        **CALLOUT_BOX_STYLE,
                    ),
                    spacing="7",
                    align="start",
                ),
                max_width=MAX_WIDTH,
                margin="0 auto",
                padding=PADDING_SECTION,
            ),

            # How to Access section
            rx.box(
                rx.box(
                    # Main heading (H2, not XL — subordinate to page H1)
                    rx.heading(
                        how_to_heading,
                        as_="h2",
                        margin_bottom=SPACING_LG,
                        **HEADING_LG_STYLE,
                    ),

                    # Intro paragraph
                    rx.text(
                        f"{product_name} uses regional pricing, which means the same subscription costs {cheapest_region_price_display}/month in {cheapest_region_name}\u2014significantly less than in many other countries. Here\u2019s how to access the lower price:",
                        font_size=FONT_SIZE_BASE,
                        line_height="1.7",
                        color=COLOR_TEXT_SECONDARY,
                        margin_bottom=SPACING_2XL,
                    ),

                    # What You'll Need
                    rx.heading("What You'll Need", as_="h3", margin_bottom=SPACING_LG, **HEADING_MD_STYLE),
                    rx.box(
                        rx.text(f"\u2022 VPN service with servers in {cheapest_region_name}", **BODY_TEXT_STYLE, margin_bottom=SPACING_SM),
                        rx.text("\u2022 International Visa or Mastercard (Wise or Revolut also work well)", **BODY_TEXT_STYLE, margin_bottom=SPACING_SM),
                        rx.text("\u2022 10\u201315 minutes to walk through the setup", **BODY_TEXT_STYLE),
                        margin_bottom=SPACING_2XL,
                    ),

                    # Step-by-Step Instructions
                    rx.heading("Step-by-Step Instructions", as_="h3", margin_bottom=SPACING_LG, **HEADING_MD_STYLE),
                    rx.box(
                        # Step 1
                        rx.box(
                            rx.text("1.", **STEP_NUMBER_STYLE),
                            rx.text("Get a VPN subscription with reliable servers in the cheapest region.", **BODY_TEXT_STYLE, margin_bottom=SPACING_XS),
                            rx.link(
                                f"\u2192 Get NordVPN (best VPN for {product_name})",
                                href=vpn_affiliate_link,
                                **LINK_STYLE,
                                **BODY_TEXT_STYLE,
                            ),
                            margin_bottom=SPACING_XL,
                        ),

                        # Step 2
                        rx.box(
                            rx.text("2.", **STEP_NUMBER_STYLE),
                            rx.text(
                                f"Open your VPN app and connect to a server located in {cheapest_region_name}. Wait a few seconds until the VPN confirms the connection.",
                                **BODY_TEXT_STYLE,
                            ),
                            margin_bottom=SPACING_XL,
                        ),

                        # Step 3
                        rx.box(
                            rx.text("3.", **STEP_NUMBER_STYLE),
                            rx.text(
                                "Clear your browser cookies and cached files for the last 24 hours. Using an incognito or private window works just as well.",
                                **BODY_TEXT_STYLE,
                            ),
                            margin_bottom=SPACING_XL,
                        ),

                        # Step 4
                        rx.box(
                            rx.text("4.", **STEP_NUMBER_STYLE),
                            rx.text(
                                f"Visit the {cheapest_region_name} version of the {product_name} website while the VPN stays on. The pricing should now reflect that region.",
                                **BODY_TEXT_STYLE,
                            ),
                            margin_bottom=SPACING_XL,
                        ),

                        # Step 5
                        rx.box(
                            rx.text("5.", **STEP_NUMBER_STYLE),
                            rx.text(
                                f"Checkout using an international payment method. Make sure the card allows transactions in {cheapest_region_name}. Wise or Revolut are handy backup options.",
                                **BODY_TEXT_STYLE,
                            ),
                            margin_bottom=SPACING_XL,
                        ),

                        # Step 6
                        rx.box(
                            rx.text("6.", **STEP_NUMBER_STYLE),
                            rx.text(
                                f"Once payment succeeds, enjoy {product_name} at the lower {cheapest_region_name} price\u2014VPN only needed for signup unless you want to keep browsing from that region.",
                                **BODY_TEXT_STYLE,
                            ),
                        ),
                        margin_bottom=SPACING_2XL,
                    ),

                    # Important Notes — left-border accent for visual distinction
                    rx.heading("Important Notes", as_="h3", margin_bottom=SPACING_LG, **HEADING_MD_STYLE),
                    rx.box(
                        rx.text("\u2022 Terms of Service: Using a VPN to access regional pricing may conflict with the provider\u2019s policies. Review the risks before moving ahead.", **BODY_TEXT_STYLE, margin_bottom=SPACING_SM),
                        rx.text(f"\u2022 Payment continuity: Check that your payment method will keep working for future {product_name} renewals.", **BODY_TEXT_STYLE, margin_bottom=SPACING_SM),
                        rx.text("\u2022 VPN cost: Remember to factor the VPN subscription into your overall savings.", **BODY_TEXT_STYLE),
                        border_left=f"3px solid {COLOR_BLACK}",
                        padding_left=SPACING_LG,
                        padding_y=SPACING_MD,
                        background=COLOR_BACKGROUND_ALT,
                    ),

                    max_width=MAX_WIDTH,
                    margin="0 auto",
                    padding=PADDING_SECTION,
                ),
            ),

            # FAQ section
            faq_section(),

            # Footer
            site_footer(),
        )
    return page

    

class State(rx.State):
    @rx.var
    def current_year(self) -> str:
        """Get the current year"""
        import datetime
        return str(datetime.datetime.now().year)

def pricing_table(data: list[dict]) -> rx.Component:
    """Clean pricing table for a specific product"""
    from .design_constants import BODY_TEXT_STYLE, LINK_STYLE, COLOR_BORDER
    rows = []
    for i, item in enumerate(data):
        rows.append(
            rx.table.row(
                rx.table.cell(
                    rx.text(str(i + 1), text_align="center", **BODY_TEXT_STYLE),
                ),
                rx.table.cell(
                    rx.link(
                        rx.text(item["region_name"], **BODY_TEXT_STYLE),
                        href=f"/{item['slug']}",
                        **LINK_STYLE,
                    ),
                ),
                rx.table.cell(
                    rx.text(item["price_display"], text_align="right", **BODY_TEXT_STYLE),
                ),
            )
        )
    return rx.box(
        rx.table.root(
            rx.table.body(*rows),
        ),
        width="100%",
        border_top=f"1px solid {COLOR_BORDER}",
    )

def health() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.text("healthy"),
                spacing="5",
                padding_y="4rem",
            ),
            max_width="1200px",
            margin="0 auto",
            padding_x="1.5rem",
            width="100%",
        ),
        spacing="0",
        align="stretch",
        min_height="100vh",
    )

def not_found(page_text) -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.heading(page_text, as_="h1"),
                spacing="5",
                padding_y="4rem",
            ),
            max_width="1200px",
            margin="0 auto",
            padding_x="1.5rem",
            width="100%",
        ),
        spacing="0",
        align="stretch",
        min_height="100vh",
    )