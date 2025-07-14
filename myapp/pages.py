from rxconfig import config
import reflex as rx
import json
import os

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

def index() -> rx.Component:
    return rx.fragment(
        rx.color_mode_button(rx.color_mode_icon(), float="right"),
        rx.vstack(
            rx.heading("Cheapest country for Creative Cloud All Apps — 2025", font_size="2em"),
            rx.table_container(
                rx.table(
                    rx.thead(
                        rx.tr(
                            rx.th("Country", font_weight="bold"),
                            rx.th("Monthly Price", font_weight="bold"),
                        )
                    ),
                    rx.tbody(
                        rx.foreach(
                            State.pricing_data,
                            lambda item, index: rx.tr(
                                rx.td(
                                    item["region_name"],
                                    font_weight=rx.cond(index == 0, "bold", "normal"),
                                    color=rx.cond(index == 0, "green.500", "inherit")
                                ),
                                rx.td(
                                    item["price_display"],
                                    font_weight=rx.cond(index == 0, "bold", "normal"),
                                    color=rx.cond(index == 0, "green.500", "inherit")
                                ),
                            )
                        )
                    ),
                    variant="striped",
                    size="lg",
                ),
                width="100%",
                overflow_x="auto",
            ),
            rx.text("Save up to 80%", font_size="1.2em"),
            rx.button(
                "Unlock cheapest price with NordVPN",
                size="lg",
                color_scheme="purple",
                padding="1em 2em",
                border_radius="0.5em",
                font_weight="bold",
                _hover={
                    "transform": "translateY(-2px)",
                    "box-shadow": "0 4px 12px rgba(107,99,246,0.3)",
                },
            ),
            rx.heading("Creative Cloud All Apps Global Pricing Guide 2025 – How to Pay Less with a VPN", font_size="1.5em", as_="h2"),
            rx.text("Did you know that the cost of [ServiceName] can vary significantly depending on where you buy it? In fact, the exact same subscription might be available in another country for only a fraction of what you’re paying now. This guide will show you how global pricing works for [ServiceName] and how to take advantage of it. By using a reliable VPN (Virtual Private Network), you can unlock lower regional prices for [ServiceName] without compromising on access or quality. Read on to learn how to save money on [ServiceName] in 2025 while still enjoying all its benefits!", font_size="0.5em"),
            rx.heading("[ServiceName] Price Around the World", font_size="0.7em", as_="h3"),
            rx.text("Pricing for *[ServiceName]* isn’t the same everywhere – it’s a classic case of regional pricing (also known as price discrimination). Companies often charge different prices in different countries based on factors like local income levels, competition, or market strategy. This means users in lower-income regions often pay *much less* for the same service than those in wealthier regions. For example, popular streaming and software subscriptions show huge price gaps across countries. Netflix’s premium plan is about **$19.99** per month in the U.S. but under **$5** in Turkey! Similarly, Spotify Premium costs around **$10.99** in the US, yet users in Turkey pay roughly **$2.50** for the same plan. These disparities present a big opportunity: by virtually “shopping” from a cheaper country, you could **save 50–80%** on your *[ServiceName]* subscription. **Which countries are cheapest for [ServiceName]?** While it varies by product, certain regions consistently offer lower prices. In general, **countries like Argentina, Brazil, India, Turkey, and Indonesia tend to have the lowest prices** for many digital services. By contrast, wealthier markets (e.g. the USA, Canada, Western Europe, Australia) or smaller high-income countries (like Switzerland or Denmark) often have the *highest* prices. *[ServiceName]* likely follows this trend: you might find its cheapest monthly rate in a country such as **Turkey or India**, potentially at just a few dollars, whereas the most expensive rates could be in the **US or Europe**.", font_size="0.5em"),
            rx.heading("Why Does [ServiceName] Cost More or Less Depending on Country?", font_size="0.7em", as_="h3"),
            rx.text("You might wonder *why* such price differences exist. The answer lies in companies’ pricing strategies. Many services use **regional pricing** to make their products affordable in markets with lower incomes. This is a form of price discrimination: for instance, a streaming plan might be set at just a couple of dollars in India (to match local purchasing power) but is over $10 in the US, where consumers are used to higher prices. Other factors include currency exchange rates, local taxes, and competition. The key point is that the **content or service is usually identical** – you’re just paying a different amount for it based on where the purchase is made. *[ServiceName]* likely has the **same features or library** for subscribers globally, but if you subscribe from a low-cost country, you get the **same product for less**. Companies accept this trade-off because they’d rather gain customers in emerging markets at lower prices than have none at all. For consumers like us, it means an opportunity to legitimately subscribe at a **bargain price** by choosing the right country.", font_size="0.5em"),
            # Footer
            rx.box(
                rx.vstack(
                    # Main footer content
                    rx.vstack(
                        # Footer heading
                        rx.heading(
                            "PriceDuck", 
                            size="lg", 
                            color="gray.800",
                            font_weight="bold",
                            margin_bottom="1em"
                        ),
                        
                        # Navigation section
                        rx.vstack(
                            rx.heading(
                                "Quick Links", 
                                size="sm", 
                                color="gray.700",
                                margin_bottom="0.5em"
                            ),
                            rx.hstack(
                                rx.link(
                                    "Home", 
                                    href="/", 
                                    color="blue.600",
                                    _hover={"color": "blue.800", "text_decoration": "underline"}
                                ),
                                rx.link(
                                    "About", 
                                    href="/about", 
                                    color="blue.600",
                                    _hover={"color": "blue.800", "text_decoration": "underline"}
                                ),
                                rx.link(
                                    "Contact", 
                                    href="mailto:tylermyeo@gmail.com", 
                                    color="blue.600",
                                    _hover={"color": "blue.800", "text_decoration": "underline"}
                                ),
                                spacing="2em",
                                justify="center",
                                wrap="wrap",
                            ),
                            rx.hstack(
                                rx.link(
                                    "Privacy Policy", 
                                    href="/privacy", 
                                    color="blue.600",
                                    _hover={"color": "blue.800", "text_decoration": "underline"}
                                ),
                                rx.link(
                                    "Terms of Service", 
                                    href="/terms", 
                                    color="blue.600",
                                    _hover={"color": "blue.800", "text_decoration": "underline"}
                                ),
                                spacing="2em",
                                justify="center",
                                wrap="wrap",
                                margin_top="0.5em"
                            ),
                            align="center",
                            spacing="0.5em",
                            margin_bottom="2em"
                        ),
                        
                        # Disclaimer section
                        rx.vstack(
                            rx.heading(
                                "Legal", 
                                size="sm", 
                                color="gray.700",
                                margin_bottom="0.5em"
                            ),
                            rx.text(
                                "Disclosure: This website contains affiliate links. We may earn a commission if you make a purchase through these links, at no additional cost to you.",
                                font_size="sm",
                                color="gray.600",
                                text_align="center",
                                max_width="700px",
                                line_height="1.5"
                            ),
                            align="center",
                            margin_bottom="2em"
                        ),
                        
                        align="center",
                        spacing="1em"
                    ),
                    
                    # Copyright bar
                    rx.divider(color="gray.300", margin_y="1.5em"),
                    rx.text(
                        f"© {State.current_year} PriceDuck. All rights reserved.",
                        font_size="sm", 
                        color="gray.500",
                        text_align="center",
                    ),
                    
                    spacing="1em",
                    align="center",
                    width="100%"
                ),
                margin_top="4em",
                padding="3em 2em 2em 2em",
                bg="gray.50",
                border_top="1px solid #e2e8f0",
                width="100%"
            ),
            
            spacing="1.5em",
            font_size="2em",
            padding_top="10%",
            padding_bottom="5%",
            padding_left="10%",
            padding_right="10%",
        ),
    )

def health() -> rx.Component:
    return rx.text("healthy")

def not_found(page_text) -> rx.Component:
    return rx.fragment(
        rx.color_mode_button(rx.color_mode_icon(), float="right"),
        rx.vstack(
            rx.heading(page_text, font_size="2em"),
            spacing="1.5em",
            padding_top="10%",
        ),
    )