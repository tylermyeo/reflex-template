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
    badge, BorderRadius
)

docs_url = "https://reflex.dev/docs/getting-started/introduction"
filename = f"{config.app_name}/{config.app_name}.py"

# Function to load and process pricing data from JSON
def load_pricing_data():
    """Load pricing data from JSON file and process it"""
    try:
        data_path = os.path.join(os.path.dirname(__file__), "data", "pricing.json")
        with open(data_path, "r") as f:
            raw_data = json.load(f)
        
        # Process the data
        processed_data = {}
        
        for item in raw_data:
            region_name = item.get("region_name", "").strip()
            amount = item.get("amount", 0)
            timestamp = item.get("timestamp", "")
            
            # Skip if no region name or amount
            if not region_name or not amount:
                continue
                
            # Skip non-English characters (basic check for Arabic/other scripts)
            if not all(ord(char) < 128 for char in region_name):
                continue
                
            # Convert amount to float and format
            try:
                amount_float = float(amount)
                if amount_float <= 0:
                    continue
            except (ValueError, TypeError):
                continue
            
            # Keep only the most recent entry for each region
            if region_name not in processed_data or timestamp > processed_data[region_name]["timestamp"]:
                processed_data[region_name] = {
                    "region_name": region_name,
                    "amount": amount_float,
                    "price_display": f"${amount_float:.2f}",
                    "timestamp": timestamp
                }
        
        # Convert to list and sort by price (cheapest first)
        result = list(processed_data.values())
        result.sort(key=lambda x: x["amount"])
        
        # Return only top 10
        return result[:10]
        
    except Exception as e:
        print(f"Error loading pricing data: {e}")
        # Fallback data if file doesn't exist
        return [
            {"region_name": "Turkey", "amount": 12.99, "price_display": "$12.99"},
            {"region_name": "India", "amount": 15.99, "price_display": "$15.99"},
            {"region_name": "Brazil", "amount": 19.99, "price_display": "$19.99"},
        ]

class State(rx.State):
    # Load pricing data with proper type annotation
    pricing_data: list[dict] = load_pricing_data()
    
    @rx.var
    def current_year(self) -> str:
        """Get the current year"""
        import datetime
        return str(datetime.datetime.now().year)

def pricing_table() -> rx.Component:
    """Clean pricing table without callout card"""
    return rx.box(
        styled_table(
            table_header(
                table_header_cell("Rank", text_align="center"),
                table_header_cell("Country"),
                table_header_cell("Monthly Price", text_align="right"),
            ),
            rx.tbody(
                rx.foreach(
                    State.pricing_data,
                    lambda item, index: rx.tr(
                        table_cell(
                            rx.cond(
                                index == 0,
                                badge("1", variant="success"),
                                rx.text(index + 1, text_align="center", font_weight=Typography.WEIGHT_MEDIUM, color=Colors.GRAY_700)
                            ),
                            text_align="center",
                        ),
                        table_cell(
                            rx.cond(
                                index == 0,
                                rx.hstack(
                                    body_text(item["region_name"], 
                                             font_weight=Typography.WEIGHT_BOLD,
                                             color=Colors.SUCCESS),
                                    rx.text("🏆", font_size="16px"),
                                    spacing=Spacing.SM,
                                    align="center",
                                ),
                                body_text(item["region_name"], font_weight=Typography.WEIGHT_MEDIUM)
                            ),
                        ),
                        table_cell(
                            rx.cond(
                                index == 0,
                                body_text(item["price_display"], 
                                         font_weight=Typography.WEIGHT_BOLD,
                                         color=Colors.SUCCESS,
                                         text_align="right"),
                                body_text(item["price_display"], 
                                         font_weight=Typography.WEIGHT_MEDIUM,
                                         color=Colors.GRAY_700,
                                         text_align="right")
                            ),
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
        rx.vstack(
            # Header
            header(),
            
            # Hero section (full width)
            hero_section(
                rx.vstack(
                    heading_1("Cheapest country for", margin_bottom="0"),
                    heading_1("Creative Cloud All Apps", margin_bottom="0"), 
                    heading_1("2025", margin_bottom=Spacing.LG),
                    spacing=Spacing.XS,
                ),
                body_text(
                            "Did you know that the cost of Creative Cloud can vary significantly depending on where you buy it? In fact, the exact same subscription might be available in another country for only a fraction of what you're paying now. This guide will show you how global pricing works for Creative Cloud and how to take advantage of it. By using a reliable VPN (Virtual Private Network), you can unlock lower regional prices for Creative Cloud without compromising on access or quality. Read on to learn how to save money on Creative Cloud in 2025 while still enjoying all its benefits!",
                            margin_bottom=Spacing.LG,
                        ),
                
                # Cheapest price callout card
                rx.box(
                    rx.vstack(
                        rx.cond(
                            State.pricing_data,
                            rx.vstack(
                                body_text_small("CHEAPEST OPTION", 
                                               color=Colors.PRIMARY, 
                                               font_weight=Typography.WEIGHT_BOLD,
                                               text_transform="uppercase",
                                               letter_spacing="0.1em"),
                                heading_1(State.pricing_data[0]["region_name"], 
                                         color=Colors.PRIMARY,
                                         margin_bottom="0",
                                         font_size=Typography.TEXT_2XL,
                                         text_transform="uppercase",
                                         font_weight=Typography.WEIGHT_BOLD),
                                heading_1(State.pricing_data[0]["price_display"], 
                                         color=Colors.PRIMARY,
                                         margin_bottom="0",
                                         font_size=Typography.TEXT_5XL),
                                body_text("PER MONTH", color=Colors.PRIMARY, font_size=Typography.TEXT_SM),
                                rx.link(
                                    cta_button(
                                        "Unlock This Price with NordVPN",
                                        size="lg",
                                    ),
                                    href="https://go.nordvpn.net/aff_c?offer_id=15&aff_id=120959&url_id=902",
                                    is_external=True,
                                    text_decoration="none",
                                ),
                                body_text_small("UP TO 70% OFF", 
                                               color=Colors.PRIMARY, 
                                               font_weight=Typography.WEIGHT_BOLD,
                                               text_transform="uppercase",
                                               letter_spacing="0.1em"),
                                spacing=Spacing.SM,
                                align="center",
                            ),
                            rx.text("Loading..."),
                        ),
                        spacing=Spacing.SM,
                        align="center",
                    ),
                    background_color=Colors.LIGHT_GREEN,
                    border=f"2px solid {Colors.PRIMARY}",
                    border_radius=BorderRadius.XXXL,
                    padding=Spacing.XL,
                    max_width="800px",
                ),
            ),
            
            # Main content
            rx.box(
                content_section(
                    # Pricing table section
                    section(
                        heading_2("Top 10 cheapest countries for Creative Cloud All Apps"),
                        pricing_table(),
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