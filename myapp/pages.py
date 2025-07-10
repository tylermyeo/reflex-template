from rxconfig import config
import reflex as rx
import plotly.graph_objects as go

docs_url = "https://reflex.dev/docs/getting-started/introduction"
filename = f"{config.app_name}/{config.app_name}.py"

# Add state and page to the app.

class State(rx.State):
    # The app state
    pass

# Create a plotly figure
def create_price_chart():
    # Dummy data for Creative Cloud prices by country
    countries = ["Turkey", "India", "Brazil", "Mexico", "Argentina", "Colombia", "Chile", "Peru"]
    prices = [12.99, 15.99, 19.99, 24.99, 29.99, 34.99, 39.99, 44.99]

    # Create a horizontal bar chart
    fig = go.Figure(data=[
        go.Bar(
            y=countries,
            x=prices,
            orientation='h',
            marker_color='rgb(107,99,246)',
            text=[f"${price}" for price in prices],
            textposition='auto',
        )
    ])

    # Update the layout
    fig.update_layout(
        title="Creative Cloud All Apps Prices by Country",
        xaxis_title="Price ($)",
        yaxis_title="Country",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )

    return fig

def index() -> rx.Component:
    return rx.fragment(
        rx.color_mode_button(rx.color_mode_icon(), float="right"),
        rx.vstack(
            rx.heading("Cheapest country for Creative Cloud All Apps — 2025", font_size="2em"),
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
            rx.plotly(data=create_price_chart(), width="100%", height="400px"),
            rx.heading("Creative Cloud All Apps Global Pricing Guide 2025 – How to Pay Less with a VPN", font_size="1.5em", as_="h2"),
            rx.text("Did you know that the cost of [ServiceName] can vary significantly depending on where you buy it? In fact, the exact same subscription might be available in another country for only a fraction of what you’re paying now. This guide will show you how global pricing works for [ServiceName] and how to take advantage of it. By using a reliable VPN (Virtual Private Network), you can unlock lower regional prices for [ServiceName] without compromising on access or quality. Read on to learn how to save money on [ServiceName] in 2025 while still enjoying all its benefits!", font_size="0.7em"),
            spacing="1.5em",
            font_size="2em",
            padding_top="10%",
            padding_bottom="10%",
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