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

# Google Analytics configuration
def google_analytics():
    """Create Google Analytics tracking components"""
    return [
        # Google Analytics script
        rx.script(src="https://www.googletagmanager.com/gtag/js?id=G-QK7PNNWCBW", async_=True),
        # Google Analytics initialization
        rx.script("""
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', 'G-QK7PNNWCBW');
        """),
    ]

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
    # Add Google Analytics to the head of every page
    head_components=google_analytics(),
)

# Homepage with SEO optimization
app.add_page(
    index,
    route="/",
    title="Cheapest Country for Creative Cloud All Apps — 2025 | PriceDuck",
    description="Discover the cheapest countries to buy Creative Cloud All Apps in 2025. Save up to 80% on your Adobe subscription with our comprehensive pricing guide and VPN setup tutorial.",
    meta=[
        # Google Search Console verification
        {"name": "google-site-verification", "content": "kfPEJH3QDn4PcyoAzP3oUpaNysnWE3Esz3yiBXzZlqo"},
        
        # Basic SEO
        {"name": "keywords", "content": "creative cloud pricing, adobe subscription discount, cheapest creative cloud, creative cloud vpn, global pricing creative cloud, save money adobe"},
        {"name": "author", "content": "PriceDuck"},
        {"name": "robots", "content": "index, follow"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        
        # Open Graph (Social Sharing)
        {"property": "og:title", "content": "Cheapest Country for Creative Cloud All Apps — 2025 | PriceDuck"},
        {"property": "og:description", "content": "Save up to 80% on Creative Cloud by choosing the right country. Complete pricing guide and VPN setup tutorial included."},
        {"property": "og:type", "content": "website"},
        {"property": "og:url", "content": "https://www.priceduck.co.za"},
        {"property": "og:image", "content": "https://www.priceduck.co.za/og-image.jpg"},
        {"property": "og:site_name", "content": "PriceDuck"},
        
        # Twitter Card
        {"name": "twitter:card", "content": "summary_large_image"},
        {"name": "twitter:title", "content": "Cheapest Country for Creative Cloud All Apps — 2025"},
        {"name": "twitter:description", "content": "Save up to 80% on Creative Cloud by choosing the right country. Complete pricing guide included."},
        {"name": "twitter:image", "content": "https://www.priceduck.co.za/og-image.jpg"},
        
        # Additional SEO
        {"name": "theme-color", "content": "#8B5CF6"},
        {"name": "language", "content": "English"},
        {"name": "revisit-after", "content": "7 days"},
    ]
)

# Health page (hidden from search engines)
app.add_page(
    health,
    route="/health", 
    title="Health Check | PriceDuck",
    description="System health status",
    meta=[{"name": "robots", "content": "noindex, nofollow"}]
)

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
