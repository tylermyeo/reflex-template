# Welcome to Reflex! This file outlines the steps to create a basic app

import reflex as rx

from .pages import index
from .pages import health
from .pages import not_found

from .api import root

# Custom style with Bricolage Grotesque font
custom_style = {
    "@import": "url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,200..800&display=swap')",
    "body": {
        "font_family": "'Bricolage Grotesque', sans-serif",
        "font_weight": 700,
        "font_style": "normal",
        "font_optical_sizing": "auto",
        "font_variation_settings": "'wdth' 100",
        "margin": "0",
        "padding": "0",
        "color": "#374151",
    },
}

app = rx.App(
    style={
        "font_family": "'Bricolage Grotesque', sans-serif",
        "font_optical_sizing": "auto", 
        "font_variation_settings": "'wdth' 100",
        "color": "#374151",
    },
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wdth,wght@12..96,75..100,200..800&display=swap",
    ],
)

app.add_page(index)
app.add_page(health)

app.api.add_api_route(
    path="/",
    endpoint=root
)

not_found_text = "The page you were looking for could not be found"

app.add_custom_404_page(
    title="404 - Page Not Found", 
    description=not_found_text,
    component=not_found(not_found_text)
)

app.compile()
