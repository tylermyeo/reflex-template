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

def index() -> rx.Component:
    return main_layout(
        # Fixed header
        header(),
        
        # Main content with top padding for fixed header
        rx.box(
            rx.vstack(
                # Hero section (full width) - reduced padding by 33%
                hero_section(
                    rx.vstack(
                        heading_1("Cheapest country for", margin_bottom="0"),
                        heading_1("Creative Cloud All Apps", margin_bottom=Spacing.LG), 
                        spacing=Spacing.XS,
                    ),
                body_text(
                            "Creative Cloud All Apps costs less in some places. Find the cheapest price here.",
                            margin_bottom=Spacing.LG,
                        ),
                    padding=f"{Spacing.XXXL} 0",  # Reduced from XXXXL to XXXL (33% reduction)
                ),
            
            # Main content
            rx.box(
                content_section(
                    # Price callout card moved from hero to main content
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
                    
                    # Content sections                
                    section(
                        heading_2("Creative Cloud Price Around the World"),
                        
                        body_text(
                            "Pricing for Creative Cloud isn't the same everywhere – it's a classic case of regional pricing (also known as price discrimination). Companies often charge different prices in different countries based on factors like local income levels, competition, or market strategy. This means users in lower-income regions often pay much less for the same service than those in wealthier regions.",
                            margin_bottom=Spacing.MD,
                        ),
                        
                        body_text(
                            "For example, popular streaming and software subscriptions show huge price gaps across countries. Netflix's premium plan is about $19.99 per month in the U.S. but under $5 in Turkey! Similarly, Spotify Premium costs around $10.99 in the US, yet users in Turkey pay roughly $2.50 for the same plan. These disparities present a big opportunity: by virtually \"shopping\" from a cheaper country, you could save 50–80% on your Creative Cloud subscription.",
                            margin_bottom=Spacing.MD,
                        ),
                        
                        body_text(
                            "Which countries are cheapest for Creative Cloud? While it varies by product, certain regions consistently offer lower prices. In general, countries like Argentina, Brazil, India, Turkey, and Indonesia tend to have the lowest prices for many digital services. By contrast, wealthier markets (e.g. the USA, Canada, Western Europe, Australia) or smaller high-income countries (like Switzerland or Denmark) often have the highest prices.",
                            margin_bottom=Spacing.MD,
                        ),
                        
                        body_text(
                            "Creative Cloud likely follows this trend: you might find its cheapest monthly rate in a country such as Turkey or India, potentially at just a few dollars, whereas the most expensive rates could be in the US or Europe.",
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
                ),
                flex="1",
            ),
            
            # Footer
            footer(),
            
            spacing="0",
            align="stretch",
            min_height="100vh",
        ),
        padding_top="36px",  # Add top padding for fixed header
    )
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