from rxconfig import config
import reflex as rx
import json
import os

# Import our design system
from .styles import (
    Colors, Typography, Spacing,
    heading_1, heading_2, heading_3, body_text, body_text_large, body_text_small,
    cta_button, card, container, section,
    styled_table, table_header, table_header_cell, table_cell,
    success_text, page_wrapper, content_section, hero_section,
    main_layout, header, footer,
    badge, BorderRadius, callout_card_latest, callout_card_cheapest, table_callout_card, text_link
)
from .styles.theme import Animation

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
        return main_layout(
        # Header
        header(),
        
        # Page content
        rx.box(
            rx.vstack(
                # Hero section (full width) - reduced padding by 33%
                hero_section(
                    rx.vstack(
                        heading_1(title),
                        body_text(intro), 
                        spacing=Spacing.XS,
                    ),
                    padding=f"{Spacing.XXXL} 0",
                ),
            
            # Main content
            rx.box(
                content_section(
                    callout_card_latest(
                        "LATEST PRICE",
                        region_name,
                        latest_price_display,
                        last_price_update,
                    ),
                    rx.cond(
                        State.pricing_data,
                        callout_card_cheapest(
                            "CHEAPEST PRICE",
                            State.cheapest_region_name,
                            State.cheapest_price_display,
                        ),
                        callout_card_cheapest(
                            "CHEAPEST PRICE",
                            "Loading...",
                            "Loading...",
                        ),
                    ),
                    
                    # Table callout card
                    table_callout_card(
                        rx.center(
                            section(
                                heading_2("Top 10 cheapest countries for Creative Cloud All Apps",
                                            margin_bottom=Spacing.XL),
                                pricing_table(),
                            ),
                            width="100%",
                        ),
                    ),
                ),
                
                # Content sections
                section(
                    heading_2(how_to_heading),
                    body_text(
                        f"{product_name} uses regional pricing, which means the same subscription costs {cheapest_region_price_display}/month in {cheapest_region_name}—significantly less than in many other countries. Here's how to access the lower price:",
                        margin_bottom=Spacing.LG,
                    ),
                    heading_3("What You'll Need", margin_bottom=Spacing.SM),
                    rx.unordered_list(
                        rx.list_item(
                            body_text(
                                f"A VPN service with servers in {cheapest_region_name}",
                                margin_bottom=Spacing.XS,
                            )
                        ),
                        rx.list_item(
                            body_text(
                                "An international Visa or Mastercard (Wise or Revolut also work well)",
                                margin_bottom=Spacing.XS,
                            )
                        ),
                        rx.list_item(
                            body_text(
                                "10–15 minutes to walk through the setup",
                                margin_bottom=Spacing.XS,
                            )
                        ),
                        padding_left=Spacing.LG,
                        margin_bottom=Spacing.LG,
                    ),
                    heading_3("Step-by-Step Instructions", margin_bottom=Spacing.SM),
                    body_text(
                        f"Follow these simple steps to unlock the {cheapest_region_name} rate for {product_name}.",
                        margin_bottom=Spacing.MD,
                    ),
                    rx.ordered_list(
                        rx.list_item(
                            rx.vstack(
                                body_text(
                                    "Get a VPN subscription with reliable servers in the cheapest region.",
                                    margin_bottom=Spacing.XS,
                                ),
                                text_link(
                                    f"Get NordVPN (best VPN for {product_name})",
                                    href=vpn_affiliate_link,
                                ),
                            ),
                            margin_bottom=Spacing.MD,
                        ),
                        rx.list_item(
                            body_text(
                                f"Open your VPN app and connect to a server located in {cheapest_region_name}. Wait a few seconds until the VPN confirms the connection.",
                                margin_bottom=Spacing.MD,
                            ),
                        ),
                        rx.list_item(
                            body_text(
                                "Clear your browser cookies and cached files for the last 24 hours. Using an incognito or private window works just as well.",
                                margin_bottom=Spacing.MD,
                            ),
                        ),
                        rx.list_item(
                            body_text(
                                f"Visit the {cheapest_region_name} version of the {product_name} website while the VPN stays on. The pricing should now reflect that region.",
                                margin_bottom=Spacing.MD,
                            ),
                        ),
                        rx.list_item(
                            body_text(
                                f"Checkout using an international payment method. Make sure the card allows transactions in {cheapest_region_name}. Wise or Revolut are handy backup options.",
                                margin_bottom=Spacing.MD,
                            ),
                        ),
                        rx.list_item(
                            body_text(
                                f"Once payment succeeds, enjoy {product_name} at the lower {cheapest_region_name} price—VPN only needed for signup unless you want to keep browsing from that region.",
                                margin_bottom=Spacing.MD,
                            ),
                        ),
                        padding_left=Spacing.LG,
                        margin_bottom=Spacing.LG,
                    ),
                    heading_3("Important Considerations", margin_bottom=Spacing.SM),
                    rx.unordered_list(
                        rx.list_item(
                            body_text(
                                "Terms of Service: Using a VPN to access regional pricing may conflict with the provider's policies. Review the risks before moving ahead.",
                                margin_bottom=Spacing.XS,
                            )
                        ),
                        rx.list_item(
                            body_text(
                                f"Payment continuity: Check that your payment method will keep working for future {product_name} renewals.",
                                margin_bottom=Spacing.XS,
                            )
                        ),
                        rx.list_item(
                            body_text(
                                "VPN cost: Remember to factor the VPN subscription into your overall savings.",
                                margin_bottom=Spacing.XS,
                            )
                        ),
                        padding_left=Spacing.LG,
                    ),
                ),
                
                section(
                    heading_2("Why Does Creative Cloud Cost More or Less Depending on Country?"),
                    
                    body_text(
                        "You might wonder why such price differences exist. The answer lies in companies' pricing strategies. Many services use regional pricing to make their products affordable in markets with lower incomes. This is a form of price discrimination: for instance, a streaming plan might be set at just a couple of dollars in India (to match local purchasing power) but is over $10 in the US, where consumers are used to higher prices.",
                        margin_bottom=Spacing.MD,
                    ),
                    
                    body_text(
                        "Other factors include currency exchange rates, local taxes, and competition. The key point is that the content or service is usually identical – you're just paying a different amount for it based on where the purchase is made. Creative Cloud likely has the same features or library for subscribers globally, but if you subscribe from a low-cost country, you get the same product for less.",
                        margin_bottom=Spacing.MD,
                    ),
                    
                    body_text(
                        "Companies accept this trade-off because they'd rather gain customers in emerging markets at lower prices than have none at all. For consumers like us, it means an opportunity to legitimately subscribe at a bargain price by choosing the right country.",
                    ),
                ),
                flex="1",
            ),
            
            # Footer
            footer(),
            
            spacing="0",
            align="stretch",
            min_height="50vh",
        ),
        padding_top="36px",  # Add top padding for header
    )
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
    return rx.box(
        styled_table(
            rx.tbody(
                rx.foreach(
                    State.pricing_data,
                    lambda item, index: rx.tr(
                        table_cell(
                            rx.text(index + 1, text_align="center"),
                            text_align="center",
                        ),
                        table_cell(
                            text_link(
                                item["region_name"],
                                href=f"/{item['slug']}",
                            ),
                        ),
                        table_cell(
                            rx.text(item["price_display"], text_align="right"),
                            text_align="right",
                        ),
                    )
                )
            ),
        ),
        border_radius=BorderRadius.LG,
        overflow="hidden",
        width="100%",
    )

def tool_pill(name: str, href: str, **props) -> rx.Component:
    """Pill-style button for tool selection"""
    default_props = {
        "background_color": Colors.PRIMARY,
        "color": Colors.WHITE,
        "font_family": Typography.FONT_FAMILY,
        "font_weight": Typography.WEIGHT_SEMIBOLD,
        "font_size": Typography.TEXT_LG,
        "padding": f"{Spacing.MD} {Spacing.XL}",
        "border_radius": BorderRadius.FULL,
        "border": "none",
        "cursor": "pointer",
        "transition": f"all {Animation.NORMAL} ease-in-out",
        "_hover": {
            "background_color": Colors.PRIMARY_HOVER,
            "transform": "translateY(-1px)",
        },
    }
    default_props.update(props)
    return rx.link(
        rx.button(name, **default_props),
        href=href,
        text_decoration="none",
        _hover={"text_decoration": "none"},
    )

def index() -> rx.Component:
    # Get cheapest country slug for Adobe Creative Cloud
    cheapest_slug = None
    if PRICING_DATA:
        cheapest_slug = f"/{PRICING_DATA[0]['slug']}"
    
    return main_layout(
        # Fixed header
        header(),
        
        # Main content with top padding for fixed header
        rx.box(
            rx.vstack(
                # 1. Hero section
                hero_section(
                    rx.vstack(
                        heading_1("Find the cheapest country for your software.", margin_bottom=Spacing.LG),
                        body_text(
                            "Software companies charge different prices in every region.",
                            margin_bottom=Spacing.MD,
                        ),
                        body_text(
                            "PriceDuck compares official prices so you can see where your tools are cheapest and buy from that country instead.",
                        ),
                        spacing=Spacing.SM,
                        align="center",
                    ),
                    padding=f"{Spacing.XXXL} 0",
                ),
                
                # 2. Find cheapest country section
                content_section(
                    section(
                        heading_2("Find cheapest country", margin_bottom=Spacing.LG),
                        body_text(
                            "Start with a tool below.",
                            margin_bottom=Spacing.MD,
                        ),
                        body_text(
                            "We'll send you straight to the country where it's currently cheapest, and you can compare against other regions from there.",
                            margin_bottom=Spacing.XL,
                        ),
                        rx.hstack(
                            *[
                                tool_pill(
                                    tool["name"],
                                    cheapest_slug if cheapest_slug else "#",
                                )
                                for tool in TOOLS_CONFIG
                            ],
                            spacing=Spacing.MD,
                            justify="center",
                            wrap="wrap",
                        ),
                        align="center",
                    ),
                ),
                
                # 3. Why PriceDuck exists section
                content_section(
                    section(
                        heading_2("Why PriceDuck exists", margin_bottom=Spacing.LG),
                        body_text(
                            "The same subscription can be much cheaper in another country, even though you get the exact same product.",
                            margin_bottom=Spacing.MD,
                        ),
                        body_text(
                            "We track official prices for popular tools across regions so you can see how much you're overpaying — and where it makes sense to switch.",
                        ),
                        align="center",
                    ),
                ),
                
                # 4. How it works section
                content_section(
                    section(
                        heading_2("How it works", margin_bottom=Spacing.LG),
                        rx.ordered_list(
                            rx.list_item(
                                body_text(
                                    "Pick a tool from the list (today: Adobe Creative Cloud All Apps).",
                                    margin_bottom=Spacing.MD,
                                ),
                            ),
                            rx.list_item(
                                body_text(
                                    "We show you the cheapest country for that tool and how it compares to other regions.",
                                    margin_bottom=Spacing.MD,
                                ),
                            ),
                            rx.list_item(
                                body_text(
                                    "You buy from that region using a VPN or local payment method, if it makes sense for you.",
                                    margin_bottom=Spacing.MD,
                                ),
                            ),
                            padding_left=Spacing.XL,
                            margin_bottom=Spacing.LG,
                        ),
                        body_text(
                            "We don't sell VPNs or payment workarounds. We just show you where the prices are different.",
                            margin_bottom=Spacing.NONE,
                        ),
                        align="center",
                    ),
                ),
                
                # 5. What's live right now section
                content_section(
                    section(
                        heading_2("What's live right now", margin_bottom=Spacing.LG),
                        body_text(
                            "PriceDuck is in early MVP.",
                            margin_bottom=Spacing.MD,
                        ),
                        body_text(
                            "We're starting with a small set of services and countries, and we'll keep expanding coverage over time.",
                            margin_bottom=Spacing.XL,
                        ),
                        
                        # Services covered
                        rx.vstack(
                            heading_3("Services covered today", margin_bottom=Spacing.SM),
                            rx.unordered_list(
                                rx.list_item(
                                    text_link(
                                        "Adobe Creative Cloud All Apps",
                                        href=cheapest_slug if cheapest_slug else "#",
                                    ),
                                ),
                                padding_left=Spacing.LG,
                                margin_bottom=Spacing.XL,
                            ),
                            align="center",
                            margin_bottom=Spacing.XL,
                        ),
                        
                        # Countries and regions
                        rx.vstack(
                            heading_3("Countries and regions", margin_bottom=Spacing.SM),
                            rx.hstack(
                                *[
                                    rx.fragment(
                                        text_link(
                                            region["name"],
                                            href=f"/{region['slug']}",
                                            font_size=Typography.TEXT_BASE,
                                        ),
                                        rx.text(" · ", color=Colors.GRAY_600, margin_x=Spacing.XS) if i < len(UNIQUE_REGIONS) - 1 else rx.fragment(),
                                    )
                                    for i, region in enumerate(UNIQUE_REGIONS)
                                ],
                                wrap="wrap",
                                justify="center",
                                align="center",
                                spacing=Spacing.NONE,
                                margin_bottom=Spacing.XL,
                            ),
                            align="center",
                        ),
                        align="center",
                    ),
                ),
                
                # Footer
                footer(),
                
                spacing="0",
                align="stretch",
                min_height="100vh",
            ),
            padding_top="36px",  # Add top padding for fixed header
        ),
    )

def health() -> rx.Component:
    return page_wrapper(
        content_section(
            body_text("healthy"),
        ),
    )

def not_found(page_text) -> rx.Component:
    return page_wrapper(
        content_section(
            heading_1(page_text),
        ),
    )