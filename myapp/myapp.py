# Welcome to Reflex! This file outlines the steps to create a basic app

import reflex as rx

from .pages_rebuilt import index
from .pages import health
from .pages import not_found
from .pages import cms_rows, make_cms_page, State

from .api import root, sitemap

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
        # Force left alignment at HTML/body level
        rx.html("""
            <style>
                html, body, #root, [data-radix-scroll-area-viewport] {
                    text-align: left !important;
                }
                h1, h2, h3, h4, h5, h6, p, div {
                    text-align: left !important;
                }
            </style>
        """),
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
    state=State,
    style={
        "font_family": "'Bricolage Grotesque', sans-serif",
        "font_optical_sizing": "auto", 
        "font_variation_settings": "'wdth' 100",
        "color": "#374151",
        "*": {
            "text_align": "left !important",
        },
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
    title="Find the cheapest country for your software | PriceDuck",
    description="Software companies charge different prices in every region. PriceDuck compares official prices so you can see where your tools are cheapest and buy from that country instead.",
    meta=[
        # Google Search Console verification
        {"name": "google-site-verification", "content": "kfPEJH3QDn4PcyoAzP3oUpaNysnWE3Esz3yiBXzZlqo"},
        
        # Basic SEO
        {"name": "keywords", "content": "regional pricing, cheapest country software, software price comparison, global software pricing, regional subscription pricing, software discounts by country, compare software prices"},
        {"name": "author", "content": "PriceDuck"},
        {"name": "robots", "content": "index, follow"},
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        
        # Open Graph (Social Sharing)
        {"property": "og:title", "content": "Find the cheapest country for your software | PriceDuck"},
        {"property": "og:description", "content": "Software companies charge different prices in every region. PriceDuck compares official prices so you can see where your tools are cheapest."},
        {"property": "og:type", "content": "website"},
        {"property": "og:url", "content": "https://www.priceduck.co.za"},
        {"property": "og:image", "content": "https://www.priceduck.co.za/og-image.jpg"},
        {"property": "og:site_name", "content": "PriceDuck"},
        
        # Twitter Card
        {"name": "twitter:card", "content": "summary_large_image"},
        {"name": "twitter:title", "content": "Find the cheapest country for your software | PriceDuck"},
        {"name": "twitter:description", "content": "Software companies charge different prices in every region. PriceDuck compares official prices across countries."},
        {"name": "twitter:image", "content": "https://www.priceduck.co.za/og-image.jpg"},
        
        # Additional SEO
        {"name": "theme-color", "content": "#8B5CF6"},
        {"name": "language", "content": "English"},
        # Removed deprecated "revisit-after" meta tag - Google ignores it
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

# Custom sitemap endpoint with weekly changefreq
app.api.add_api_route(
    path="/sitemap.xml",
    endpoint=sitemap
)

not_found_text = "The page you were looking for could not be found"

app.add_custom_404_page(
    title="404 - Page Not Found", 
    description=not_found_text,
    component=not_found(not_found_text)
)


# Dynamically add a page for each CMS row (no filters yet)
for row in cms_rows:
    slug = (row.get("Slug") or "").strip()
    if not slug:
        continue
    route = "/" + slug.lstrip("/")
    page_fn = make_cms_page(row)
    page_title = row.get("SEO Meta Title", "Untitled")
    page_desc = row.get("SEO Meta Description", "No description")
    
    app.add_page(
        page_fn, 
        route=route, 
        title=page_title, 
        description=page_desc
    )

app.compile()
