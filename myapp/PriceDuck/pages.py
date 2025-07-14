from rxconfig import config
import reflex as rx
import datetime
from .state import State


docs_url = "https://reflex.dev/docs/getting-started/introduction"
filename = f"{config.app_name}/{config.app_name}.py"


def footer():
    current_year = datetime.date.today().year
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.link("Home", href="#", font_size="0.8em"),
                rx.link("About", href="#", font_size="0.8em"),
                rx.link("Contact", href="mailto:tylermyeo@gmail.com", font_size="0.8em"),
                rx.link("Privacy Policy", href="#", font_size="0.8em"),
                rx.link("Terms of Service", href="#", font_size="0.8em"),
                spacing="2em",
                justify="center",
            ),
            rx.text(
                "This site contains affiliate links. We may earn a commission when you buy through them, at no extra cost to you.",
                font_size="0.7em",
                color="gray.500",
                text_align="center",
                padding_x="2em",
            ),
            rx.text(
                f"© {current_year} PriceDuck. All rights reserved.",
                font_size="0.7em",
                color="gray.500",
                text_align="center",
            ),
            spacing="1.5em",
            align="center",
            width="100%",
        ),
        padding_y="2em",
        padding_x="10%",
        background_color=rx.color_mode_cond(light="gray.100", dark="#1A202C"),
        border_top=rx.color_mode_cond(light="1px solid #E2E8F0", dark="1px solid #2D3748"),
        width="100%",
    )


def index() -> rx.Component:
    return rx.fragment(
        rx.color_mode_button(rx.color_mode_icon(), float="right"),
        rx.vstack(
            rx.heading(f"Cheapest country for {State.selected_product} — {datetime.date.today().year}", font_size="2em"),
            rx.text("Save up to 80%", font_size="1.2em"),
            rx.select(
                State.products,
                value=State.selected_product,
                on_change=State.set_selected_product,
                margin_bottom="1em",
            ),
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
            rx.cond(
                State.data_load_error,
                rx.alert(
                    rx.alert_icon(),
                    rx.box(
                        rx.alert_title("Data Loading Error"),
                        rx.alert_description(State.data_load_error),
                    ),
                    status="error",
                    width="100%",
                ),
            ),
            rx.heading(f"{State.selected_product} Global Pricing Guide {datetime.date.today().year} – How to Pay Less with a VPN", font_size="1.5em", as_="h2"),
            rx.text(f"Did you know that the cost of {State.selected_product} can vary significantly depending on where you buy it? [...]", font_size="0.5em"),
            rx.heading(f"{State.selected_product} Price Around the World", font_size="0.7em", as_="h3"),
            rx.text(f"Pricing for *{State.selected_product}* isn’t the same everywhere – it’s a classic case of regional pricing [...]", font_size="0.5em"),
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
                            State.product_data,
                            lambda row: rx.tr(
                                rx.td(row["Region_Name"]),
                                rx.td(f"${row['Amount']:.2f}")
                            )
                        )
                    ),
                    variant="striped",
                    size="lg",
                ),
                width="100%",
                overflow_x="auto",
            ),
            rx.heading("Why Does [ServiceName] Cost More or Less Depending on Country?", font_size="0.7em", as_="h3"),
            rx.text("You might wonder *why* such price differences exist. The answer lies in companies’ pricing strategies. Many services use **regional pricing** to make their products affordable in markets with lower incomes. This is a form of price discrimination: for instance, a streaming plan might be set at just a couple of dollars in India (to match local purchasing power) but is over $10 in the US, where consumers are used to higher prices. Other factors include currency exchange rates, local taxes, and competition. The key point is that the **content or service is usually identical** – you’re just paying a different amount for it based on where the purchase is made. *[ServiceName]* likely has the **same features or library** for subscribers globally, but if you subscribe from a low-cost country, you get the **same product for less**. Companies accept this trade-off because they’d rather gain customers in emerging markets at lower prices than have none at all. For consumers like us, it means an opportunity to legitimately subscribe at a **bargain price** by choosing the right country.", font_size="0.5em"),
            rx.heading("How to Get [ServiceName] at the Lowest Price (Step-by-Step)", font_size="0.7em", as_="h3"),
            rx.text("So, how can you actually pay the cheapest price for [ServiceName] if you're not in a cheap-region country? The answer is to use a VPN to virtually change your location during sign-up. Don't worry – it's easier than it sounds. Just follow these steps:", font_size="0.5em"),
            rx.ordered_list(
                rx.list_item(
                    rx.text(
                        rx.span("Choose a Reliable VPN Service:", font_weight="bold"),
                        " First, subscribe to a reputable VPN provider. (If you don't have one, see our recommendations below.) Download and install the VPN app on your device. ",
                        rx.span("Tip:", font_style="italic"),
                        " Use a well-known VPN with plenty of global servers; free VPNs might not work reliably for this."
                    ),
                    margin_bottom="1em",
                ),
                rx.list_item(
                    rx.text(
                        rx.span("Connect to a Low-Cost Country Server:", font_weight="bold"),
                        " Open the VPN and connect to a server in a country where ",
                        rx.span("[ServiceName]", font_style="italic"),
                        " is cheap. Common choices are ",
                        rx.span("Argentina, India, Turkey, or Brazil", font_weight="bold"),
                        ", since these are known for lower pricing. For example, if data shows Turkey has the cheapest ",
                        rx.span("[ServiceName]", font_style="italic"),
                        " rate, connect to a ",
                        rx.span("Turkish", font_weight="bold"),
                        " server."
                    ),
                    margin_bottom="1em",
                ),
                rx.list_item(
                    rx.text(
                        rx.span("Clear Your Browser Data:", font_weight="bold"),
                        " Before visiting the ",
                        rx.span("[ServiceName]", font_style="italic"),
                        " site, clear your browser's ",
                        rx.span("cookies and cache", font_weight="bold"),
                        ", or use a private/incognito window. This ensures the website doesn't remember your actual location from a previous visit."
                    ),
                    margin_bottom="1em",
                ),
                rx.list_item(
                    rx.text(
                        rx.span("Sign Up at the Lower Price:", font_weight="bold"),
                        " With the VPN on, go to the official ",
                        rx.span("[ServiceName]", font_style="italic"),
                        " website (or app) and start the subscription signup process. You should see the prices now shown in the ",
                        rx.span("local currency", font_weight="bold"),
                        " of the VPN server's country – which reflects that region's pricing. For instance, you might now see a monthly price of $3 instead of $10."
                    ),
                    margin_bottom="1em",
                ),
                rx.list_item(
                    rx.text(
                        rx.span("Complete the Purchase:", font_weight="bold"),
                        " Proceed to sign up and pay. Most services accept international ",
                        rx.span("credit/debit cards", font_weight="bold"),
                        ", so you can likely use your regular card for payment. (Some platforms may require a local payment method or gift card for that country, but many do ",
                        rx.span("accept global Visa/MasterCard", font_weight="bold"),
                        " without issue.) Once payment is done, you've locked in the cheaper rate!"
                    ),
                    margin_bottom="1em",
                ),
                rx.list_item(
                    rx.text(
                        rx.span("Enjoy [ServiceName] Anywhere:", font_weight="bold"),
                        " After subscribing, your ",
                        rx.span("[ServiceName]", font_style="italic"),
                        " account is active. Usually, you can now use ",
                        rx.span("[ServiceName]", font_style="italic"),
                        " from any country – ",
                        rx.span("with or without the VPN", font_weight="bold"),
                        " turned on – and it will function normally under the account you created. ",
                        rx.span("(One exception: if [ServiceName]'s content library differs by region, you'll see the content of whatever country you're actually in, unless you use the VPN to stream. But the ", font_style="italic"),
                        rx.span("billing price", font_weight="bold", font_style="italic"),
                        rx.span(" remains at the low rate.)", font_style="italic")
                    ),
                    margin_bottom="1em",
                ),
                spacing="1em",
                padding="1em",
                border_radius="0.5em",
                background="gray.50",
            ),
            spacing="1.5em",
            font_size="2em",
            padding_top="10%",
            padding_bottom="10%",
            padding_left="10%",
            padding_right="10%",
            on_mount=State.on_load,
        ),
        footer(),
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