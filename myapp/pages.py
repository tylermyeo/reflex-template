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

# Make rows available to myapp.py for routing
cms_rows: list[dict] = load_cms_pages()

# Derive pricing table data directly from CMS rows (exported by n8n)
def derive_pricing_from_cms(rows: list[dict]) -> list[dict]:
    items: list[dict] = []
    for row in rows:
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

# Tools config for homepage pills (MVP: hard-coded)
TOOLS_CONFIG = [
    {
        "name": "Adobe Creative Cloud All Apps",
        "href": None,  # Will be set dynamically to cheapest country slug
    },
]

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
        COLOR_TEXT_SECONDARY, COLOR_BACKGROUND_ALT, MAX_WIDTH, PADDING_SECTION
    )
    
    return rx.box(
        rx.box(
            rx.heading("FAQ", as_="h2", margin_bottom="3rem", **HEADING_LG_STYLE),
            *[
                rx.box(
                    rx.heading(
                        item["question"],
                        as_="h3",
                        margin_bottom="0.75rem",
                        **HEADING_MD_STYLE,
                    ),
                    rx.text(
                        item["answer"],
                        color=COLOR_TEXT_SECONDARY,
                        white_space="pre-line",
                        **BODY_TEXT_STYLE,
                    ),
                    margin_bottom="3rem",
                )
                for item in FAQ_ITEMS
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

    cheapest_entry = PRICING_DATA[0] if PRICING_DATA else None
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
            MAX_WIDTH, COLOR_BORDER, LETTER_SPACING_NORMAL, COLOR_TEXT_MUTED,
            HEADING_XL_STYLE, HEADING_LG_STYLE, HEADING_MD_STYLE, BODY_TEXT_STYLE, BUTTON_STYLE,
            COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BACKGROUND_ALT, PADDING_SECTION, COLOR_BLACK
        )
        from .components import site_header, site_footer
        
        return rx.fragment(
            # JSON-LD FAQPage schema
            faq_json_ld(),
            
            # Header
            site_header(),
            
            # Hero section
            rx.box(
                rx.heading(title, as_="h1", margin_bottom="1rem", **HEADING_LG_STYLE),
                rx.text(intro, **BODY_TEXT_STYLE, color=COLOR_TEXT_SECONDARY),
                max_width=MAX_WIDTH,
                margin="0 auto",
                padding=PADDING_SECTION,
            ),
                
                # Main content
                rx.box(
                    rx.vstack(
                                    # Latest price callout
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Latest Price", font_size="0.875rem", font_weight="700", color=COLOR_TEXT_SECONDARY, margin_bottom="0.5rem"),
                                            rx.heading(region_name, as_="h2", margin_bottom="0.5rem", **HEADING_MD_STYLE),
                                            rx.heading(latest_price_display, as_="h1", margin_bottom="0.5rem", **HEADING_LG_STYLE),
                                            rx.text("per month", font_size="0.875rem", color=COLOR_TEXT_SECONDARY),
                                            rx.text(f"Last updated {last_price_update}", font_size="0.875rem", color=COLOR_TEXT_MUTED, margin_top="0.5rem"),
                                            spacing="0.25rem",
                                            align="start",
                                            width="100%",
                    ),
                                        background=COLOR_BACKGROUND_ALT,
                                        padding="2rem",
                                        width="100%",
                                    ),
                                    
                                    # Cheapest price callout
                                    rx.box(
                                        rx.vstack(
                                            rx.text("Cheapest Price", font_size="0.875rem", font_weight="700", color=COLOR_TEXT_SECONDARY, margin_bottom="0.5rem"),
                                            rx.heading(State.cheapest_region_name, as_="h2", margin_bottom="0.5rem", **HEADING_MD_STYLE),
                                            rx.heading(State.cheapest_price_display, as_="h1", margin_bottom="0.5rem", **HEADING_LG_STYLE),
                                            rx.text("per month", font_size="0.875rem", color=COLOR_TEXT_SECONDARY, margin_bottom="1rem"),
                                            rx.link(
                                                rx.box(
                                                    "Unlock This Price with NordVPN",
                                                    **BUTTON_STYLE,
                                                ),
                                                href="https://go.nordvpn.net/aff_c?offer_id=15&aff_id=120959&url_id=902",
                                                is_external=True,
                                                text_decoration="none",
                                            ),
                                            spacing="0.25rem",
                                            align="start",
                                            width="100%",
                                        ),
                                        background=COLOR_BACKGROUND_ALT,
                                        padding="2rem",
                                        width="100%",
                                    ),
                    
                    # Table callout card
                                    rx.box(
                                        rx.vstack(
                                            rx.heading("Top 10 cheapest countries for Creative Cloud All Apps", as_="h2", margin_bottom="2rem", **HEADING_LG_STYLE),
                                            pricing_table(),
                                            align="start",
                                            width="100%",
                                        ),
                                        background=COLOR_BACKGROUND_ALT,
                                        padding="2rem",
                                        width="100%",
                                    ),
                        spacing="3rem",
                        align="start",
                    ),
                    max_width=MAX_WIDTH,
                    margin="0 auto",
                    padding=PADDING_SECTION,
                ),
                
                # How to Access section - redesigned for scannability
                rx.box(
                    rx.box(
                        # Main heading
                        rx.heading(
                            how_to_heading,
                            as_="h2",
                            margin_bottom="1.5rem",
                            **HEADING_XL_STYLE,
                        ),
                        
                        # Intro paragraph - larger font
                        rx.text(
                            f"{product_name} uses regional pricing, which means the same subscription costs {cheapest_region_price_display}/month in {cheapest_region_name}—significantly less than in many other countries. Here's how to access the lower price:",
                            font_size="1.25rem",
                            line_height="1.6",
                            color=COLOR_TEXT_SECONDARY,
                            margin_bottom="3rem",
                        ),
                        
                        # What You'll Need
                        rx.heading("What You'll Need", as_="h2", margin_bottom="1.5rem", **HEADING_LG_STYLE),
                        rx.box(
                            rx.text(f"• VPN service with servers in {cheapest_region_name}", **BODY_TEXT_STYLE, margin_bottom="0.75rem"),
                            rx.text("• International Visa or Mastercard (Wise or Revolut also work well)", **BODY_TEXT_STYLE, margin_bottom="0.75rem"),
                            rx.text("• 10–15 minutes to walk through the setup", **BODY_TEXT_STYLE),
                            margin_bottom="3rem",
                        ),
                        
                        # Step-by-Step Instructions
                        rx.heading("Step-by-Step Instructions", as_="h2", margin_bottom="1.5rem", **HEADING_LG_STYLE),
                        rx.box(
                            # Step 1
                            rx.box(
                                rx.text("1.", font_weight="800", font_size="1.5rem", color=COLOR_TEXT_PRIMARY, margin_bottom="0.5rem"),
                                rx.text("Get a VPN subscription with reliable servers in the cheapest region.", **BODY_TEXT_STYLE, margin_bottom="0.5rem"),
                                rx.link(
                                    f"→ Get NordVPN (best VPN for {product_name})",
                                    href=vpn_affiliate_link,
                                    color=COLOR_BLACK,
                                    text_decoration="underline",
                                    _hover={"color": COLOR_TEXT_SECONDARY},
                                    **BODY_TEXT_STYLE,
                                ),
                                margin_bottom="2rem",
                            ),
                            
                            # Step 2
                            rx.box(
                                rx.text("2.", font_weight="800", font_size="1.5rem", color=COLOR_TEXT_PRIMARY, margin_bottom="0.5rem"),
                                rx.text(
                                    f"Open your VPN app and connect to a server located in {cheapest_region_name}. Wait a few seconds until the VPN confirms the connection.",
                                    **BODY_TEXT_STYLE,
                                ),
                                margin_bottom="2rem",
                            ),
                            
                            # Step 3
                            rx.box(
                                rx.text("3.", font_weight="800", font_size="1.5rem", color=COLOR_TEXT_PRIMARY, margin_bottom="0.5rem"),
                                rx.text(
                                    "Clear your browser cookies and cached files for the last 24 hours. Using an incognito or private window works just as well.",
                                    **BODY_TEXT_STYLE,
                                ),
                                margin_bottom="2rem",
                            ),
                            
                            # Step 4
                            rx.box(
                                rx.text("4.", font_weight="800", font_size="1.5rem", color=COLOR_TEXT_PRIMARY, margin_bottom="0.5rem"),
                                rx.text(
                                    f"Visit the {cheapest_region_name} version of the {product_name} website while the VPN stays on. The pricing should now reflect that region.",
                                    **BODY_TEXT_STYLE,
                                ),
                                margin_bottom="2rem",
                            ),
                            
                            # Step 5
                            rx.box(
                                rx.text("5.", font_weight="800", font_size="1.5rem", color=COLOR_TEXT_PRIMARY, margin_bottom="0.5rem"),
                                rx.text(
                                    f"Checkout using an international payment method. Make sure the card allows transactions in {cheapest_region_name}. Wise or Revolut are handy backup options.",
                                    **BODY_TEXT_STYLE,
                                ),
                                margin_bottom="2rem",
                            ),
                            
                            # Step 6
                            rx.box(
                                rx.text("6.", font_weight="800", font_size="1.5rem", color=COLOR_TEXT_PRIMARY, margin_bottom="0.5rem"),
                                rx.text(
                                    f"Once payment succeeds, enjoy {product_name} at the lower {cheapest_region_name} price—VPN only needed for signup unless you want to keep browsing from that region.",
                                    **BODY_TEXT_STYLE,
                                ),
                            ),
                            margin_bottom="3rem",
                        ),
                        
                        # Important Notes
                        rx.heading("Important Notes", as_="h2", margin_bottom="1.5rem", **HEADING_LG_STYLE),
                        rx.box(
                            rx.text("• Terms of Service: Using a VPN to access regional pricing may conflict with the provider's policies. Review the risks before moving ahead.", **BODY_TEXT_STYLE, margin_bottom="0.75rem"),
                            rx.text(f"• Payment continuity: Check that your payment method will keep working for future {product_name} renewals.", **BODY_TEXT_STYLE, margin_bottom="0.75rem"),
                            rx.text("• VPN cost: Remember to factor the VPN subscription into your overall savings.", **BODY_TEXT_STYLE),
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
    # Pricing data derived from CMS export
    pricing_data: list[dict] = PRICING_DATA
    
    @rx.var
    def current_year(self) -> str:
        """Get the current year"""
        import datetime
        return str(datetime.datetime.now().year)
    
    @rx.var
    def cheapest_price_display(self) -> str:
        """Get the cheapest price formatted without /mo"""
        if not self.pricing_data:
            return "Loading..."
        return f"${self.pricing_data[0]['amount']:.2f}"

    @rx.var
    def cheapest_region_name(self) -> str:
        """Get the region name associated with the cheapest price"""
        if not self.pricing_data:
            return "Loading..."
        return self.pricing_data[0]["region_name"]

    @rx.var
    def cheapest_region_heading(self) -> str:
        """Build the heading text using the cheapest region"""
        region = self.cheapest_region_name
        if region == "Loading...":
            return "How to access the lowest Creative Cloud pricing"
        return f"How to access {region} pricing"

def pricing_table() -> rx.Component:
    """Clean pricing table without callout card"""
    from .design_constants import BODY_TEXT_STYLE, COLOR_BLACK, COLOR_TEXT_SECONDARY
    return rx.box(
        rx.table_container(
            rx.table(
            rx.tbody(
                rx.foreach(
                    State.pricing_data,
                    lambda item, index: rx.tr(
                            rx.td(
                            rx.text(index + 1, text_align="center", **BODY_TEXT_STYLE),
                            text_align="center",
                            padding="0.75rem",
                        ),
                            rx.td(
                                rx.link(
                                    rx.text(item["region_name"], **BODY_TEXT_STYLE),
                                href=f"/{item['slug']}",
                                    color=COLOR_BLACK,
                                    text_decoration="underline",
                                    _hover={"color": COLOR_TEXT_SECONDARY},
                            ),
                                padding="0.75rem",
                        ),
                            rx.td(
                            rx.text(item["price_display"], text_align="right", **BODY_TEXT_STYLE),
                            text_align="right",
                                padding="0.75rem",
                        ),
                    )
                )
            ),
        ),
        ),
        width="100%",
    )

def tool_pill(name: str, href: str, **props) -> rx.Component:
    """Pill-style button for tool selection"""
    from .design_constants import BUTTON_STYLE
    return rx.link(
        rx.box(name, **BUTTON_STYLE, **props),
        href=href,
        text_decoration="none",
    )

def index() -> rx.Component:
    # Get cheapest country slug for Adobe Creative Cloud
    cheapest_slug = None
    if PRICING_DATA:
        cheapest_slug = f"/{PRICING_DATA[0]['slug']}"
    
    # Simple header
    header_component = rx.box(
        rx.box(
            rx.center(
                rx.link(
                    rx.heading("PriceDuck", font_size="1.5rem", font_weight="800"),
                    href="/",
                    text_decoration="none",
                    _hover={"text_decoration": "none"},
                ),
                width="100%",
                padding_y="1rem",
            ),
            max_width="1200px",
            margin="0 auto",
            padding_x="1.5rem",
            width="100%",
        ),
        position="static",
    )
    
    # Simple footer
    footer_component = rx.box(
        rx.box(
            rx.vstack(
                rx.heading("PriceDuck", font_size="1.5rem", font_weight="700", margin_bottom="1.5rem"),
                rx.vstack(
                    rx.heading("Quick Links", font_size="0.875rem", font_weight="600", margin_bottom="0.5rem", text_transform="uppercase"),
                    rx.hstack(
                        rx.link("Home", href="/", color="#115735", font_size="0.875rem", _hover={"text_decoration": "underline"}),
                        rx.link("About", href="/about", color="#115735", font_size="0.875rem", _hover={"text_decoration": "underline"}),
                        rx.link("Contact", href="mailto:tylermyeo@gmail.com", color="#115735", font_size="0.875rem", _hover={"text_decoration": "underline"}),
                        spacing="2rem",
                        justify="center",
                        wrap="wrap",
                    ),
                    rx.hstack(
                        rx.link("Privacy Policy", href="/privacy", color="#115735", font_size="0.875rem", _hover={"text_decoration": "underline"}),
                        rx.link("Terms of Service", href="/terms", color="#115735", font_size="0.875rem", _hover={"text_decoration": "underline"}),
                        spacing="2rem",
                        justify="center",
                        wrap="wrap",
                        margin_top="0.5rem",
                    ),
                    align="center",
                    spacing="0.5rem",
                    margin_bottom="3rem",
                ),
                rx.divider(margin_y="1.5rem"),
                rx.text("© 2025 PriceDuck. All rights reserved.", font_size="0.875rem", color="#6B7280", text_align="center"),
                spacing="1.5rem",
                align="center",
                width="100%",
            ),
            max_width="1200px",
            margin="0 auto",
            padding_x="1.5rem",
            width="100%",
        ),
        margin_top="6rem",
        padding="4rem 0 2rem 0",
        width="100%",
    )
    
    return rx.box(
        header_component,
        rx.box(
            rx.vstack(
                # 1. Hero section
                rx.box(
                    rx.box(
                    rx.vstack(
                            rx.heading("Find the cheapest country for your software.", as_="h1", margin_bottom="1.5rem"),
                            rx.text(
                            "Software companies charge different prices in every region.",
                                margin_bottom="1rem",
                        ),
                            rx.text(
                            "PriceDuck compares official prices so you can see where your tools are cheapest and buy from that country instead.",
                        ),
                            spacing="0.5rem",
                        align="start",
                        width="100%",
                    ),
                        max_width="1200px",
                        margin="0 auto",
                        padding_x="1.5rem",
                        width="100%",
                    ),
                    padding="4rem 0",
                ),
                
                # 2. Find cheapest country section
                rx.box(
                    rx.vstack(
                        rx.box(
                            rx.vstack(
                                rx.heading("Find cheapest country", as_="h2", margin_bottom="1.5rem"),
                                rx.text(
                            "Start with a tool below.",
                                    margin_bottom="1rem",
                        ),
                                rx.text(
                            "We'll send you straight to the country where it's currently cheapest, and you can compare against other regions from there.",
                                    margin_bottom="2rem",
                        ),
                        rx.hstack(
                            *[
                                tool_pill(
                                    tool["name"],
                                    cheapest_slug if cheapest_slug else "#",
                                )
                                for tool in TOOLS_CONFIG
                            ],
                                    spacing="1rem",
                            justify="center",
                            wrap="wrap",
                        ),
                        align="start",
                        width="100%",
                    ),
                        ),
                        spacing="2rem",
                        padding_y="4rem",
                    ),
                    max_width="1200px",
                    margin="0 auto",
                    padding_x="1.5rem",
                    width="100%",
                ),
                
                # 3. Why PriceDuck exists section
                rx.box(
                    rx.vstack(
                        rx.box(
                            rx.vstack(
                                rx.heading("Why PriceDuck exists", as_="h2", margin_bottom="1.5rem"),
                                rx.text(
                            "The same subscription can be much cheaper in another country, even though you get the exact same product.",
                                    margin_bottom="1rem",
                        ),
                                rx.text(
                            "We track official prices for popular tools across regions so you can see how much you're overpaying — and where it makes sense to switch.",
                        ),
                        align="start",
                        width="100%",
                    ),
                        ),
                        spacing="2rem",
                        padding_y="4rem",
                    ),
                    max_width="1200px",
                    margin="0 auto",
                    padding_x="1.5rem",
                    width="100%",
                ),
                
                # 4. How it works section
                rx.box(
                    rx.vstack(
                        rx.box(
                            rx.vstack(
                                rx.heading("How it works", as_="h2", margin_bottom="1.5rem"),
                        rx.ordered_list(
                            rx.list_item(
                                        rx.text(
                                    "Pick a tool from the list (today: Adobe Creative Cloud All Apps).",
                                            margin_bottom="1rem",
                                ),
                            ),
                            rx.list_item(
                                        rx.text(
                                    "We show you the cheapest country for that tool and how it compares to other regions.",
                                            margin_bottom="1rem",
                                ),
                            ),
                            rx.list_item(
                                        rx.text(
                                    "You buy from that region using a VPN or local payment method, if it makes sense for you.",
                                            margin_bottom="1rem",
                                ),
                            ),
                                    padding_left="2rem",
                                    margin_bottom="1.5rem",
                        ),
                                rx.text(
                            "We don't sell VPNs or payment workarounds. We just show you where the prices are different.",
                                    margin_bottom="0",
                        ),
                        align="start",
                        width="100%",
                    ),
                        ),
                        spacing="2rem",
                        padding_y="4rem",
                    ),
                    max_width="1200px",
                    margin="0 auto",
                    padding_x="1.5rem",
                    width="100%",
                ),
                
                # 5. What's live right now section
                rx.box(
                    rx.vstack(
                        rx.box(
                            rx.vstack(
                                rx.heading("What's live right now", as_="h2", margin_bottom="1.5rem"),
                                rx.text(
                            "PriceDuck is in early MVP.",
                                    margin_bottom="1rem",
                        ),
                                rx.text(
                            "We're starting with a small set of services and countries, and we'll keep expanding coverage over time.",
                                    margin_bottom="2rem",
                        ),
                        
                        # Services covered
                        rx.vstack(
                                    rx.heading("Services covered today", as_="h3", margin_bottom="0.5rem"),
                            rx.unordered_list(
                                rx.list_item(
                                            rx.link(
                                                rx.text("Adobe Creative Cloud All Apps"),
                                        href=cheapest_slug if cheapest_slug else "#",
                                    ),
                                ),
                                        padding_left="1.5rem",
                                        margin_bottom="2rem",
                            ),
                            align="start",
                                    margin_bottom="2rem",
                        ),
                        
                        # Countries and regions
                        rx.vstack(
                                    rx.heading("Countries and regions", as_="h3", margin_bottom="0.5rem"),
                            rx.hstack(
                                *[
                                    rx.fragment(
                                                rx.link(
                                                    rx.text(region["name"]),
                                            href=f"/{region['slug']}",
                                        ),
                                                rx.text(" · ", color="#4B5563", margin_x="0.25rem") if i < len(UNIQUE_REGIONS) - 1 else rx.fragment(),
                                    )
                                    for i, region in enumerate(UNIQUE_REGIONS)
                                ],
                                wrap="wrap",
                                justify="center",
                                align="center",
                                        spacing="0",
                                        margin_bottom="2rem",
                            ),
                            align="start",
                            width="100%",
                        ),
                        align="start",
                        width="100%",
                    ),
                ),
                        spacing="2rem",
                        padding_y="4rem",
                    ),
                    max_width="1200px",
                    margin="0 auto",
                    padding_x="1.5rem",
                    width="100%",
                ),
                
                footer_component,
                
                spacing="0",
                align="stretch",
                min_height="100vh",
            ),
            padding_top="36px",
        ),
        min_height="100vh",
    )

def health() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.text("healthy"),
                spacing="2rem",
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
                spacing="2rem",
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