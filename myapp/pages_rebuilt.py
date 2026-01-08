import reflex as rx
from .pages import FAQ_ITEMS, TOOLS_CONFIG, PRICING_DATA, UNIQUE_REGIONS, tool_pill
from .design_constants import (
    HEADING_XL_STYLE, HEADING_LG_STYLE, HEADING_MD_STYLE, BODY_TEXT_STYLE, BUTTON_STYLE,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_BACKGROUND_ALT,
    MAX_WIDTH, PADDING_SECTION, LETTER_SPACING_NORMAL, FONT_SIZE_BASE, COLOR_BLACK, COLOR_WHITE
)
from .components import site_header, site_footer

def index() -> rx.Component:
    """Polished minimal homepage - brutalist typography with proper spacing"""
    
    cheapest_slug = ""
    if PRICING_DATA:
        cheapest_slug = PRICING_DATA[0].get("slug", "")
    
    return rx.fragment(
        # Header
        site_header(),
        
        # Hero section - bold and centered
        rx.box(
            rx.box(
                rx.heading(
                    "Find the cheapest country for your software.",
                    as_="h1",
                    margin_bottom="1.5rem",
                    **HEADING_XL_STYLE,
                ),
                rx.text(
                    "Software companies charge different prices in every region.",
                    font_size="1.25rem",
                    line_height="1.6",
                    color=COLOR_TEXT_PRIMARY,
                    margin_bottom="0.75rem",
                ),
                rx.text(
                    "PriceDuck compares official prices so you can see where your tools are cheapest and buy from that country instead.",
                    font_size="1.25rem",
                    line_height="1.6",
                    color=COLOR_TEXT_SECONDARY,
                ),
                max_width=MAX_WIDTH,
                margin="0 auto",
                padding=PADDING_SECTION,
            ),
        ),
        
        # Find cheapest country
        rx.box(
            rx.box(
                rx.heading(
                    "Find cheapest country",
                    as_="h2",
                    margin_bottom="1.25rem",
                    **HEADING_LG_STYLE,
                ),
                rx.text(
                    "Start with a tool below.",
                    margin_bottom="0.5rem",
                    color=COLOR_TEXT_PRIMARY,
                    **BODY_TEXT_STYLE,
                ),
                rx.text(
                    "We'll send you straight to the country where it's currently cheapest, and you can compare against other regions from there.",
                    margin_bottom="2rem",
                    color=COLOR_TEXT_SECONDARY,
                    **BODY_TEXT_STYLE,
                ),
                rx.box(
                    rx.link(
                        rx.box(
                            "Adobe Creative Cloud All Apps",
                            **BUTTON_STYLE,
                        ),
                        href=cheapest_slug if cheapest_slug else "#",
                        text_decoration="none",
                    ),
                ),
                max_width=MAX_WIDTH,
                margin="0 auto",
                padding=PADDING_SECTION,
            ),
            background=COLOR_BACKGROUND_ALT,
        ),
        
        # Why PriceDuck exists
        rx.box(
            rx.box(
                rx.heading(
                    "Why PriceDuck exists",
                    as_="h2",
                    margin_bottom="1.25rem",
                    **HEADING_LG_STYLE,
                ),
                rx.text(
                    "The same subscription can be much cheaper in another country, even though you get the exact same product.",
                    margin_bottom="1rem",
                    color=COLOR_TEXT_PRIMARY,
                    **BODY_TEXT_STYLE,
                ),
                rx.text(
                    "We track official prices for popular tools across regions so you can see how much you're overpaying — and where it makes sense to switch.",
                    color=COLOR_TEXT_SECONDARY,
                    **BODY_TEXT_STYLE,
                ),
                max_width=MAX_WIDTH,
                margin="0 auto",
                padding=PADDING_SECTION,
            ),
        ),
        
        # How it works
        rx.box(
            rx.box(
                rx.heading(
                    "How it works",
                    as_="h2",
                    margin_bottom="2rem",
                    **HEADING_LG_STYLE,
                ),
                rx.ordered_list(
                    rx.list_item(
                        rx.text(
                            "Pick a tool from the list (today: Adobe Creative Cloud All Apps).",
                            **BODY_TEXT_STYLE,
                        ),
                        margin_bottom="1rem",
                    ),
                    rx.list_item(
                        rx.text(
                            "We show you the cheapest country for that tool and how it compares to other regions.",
                            **BODY_TEXT_STYLE,
                        ),
                        margin_bottom="1rem",
                    ),
                    rx.list_item(
                        rx.text(
                            "You buy from that region using a VPN or local payment method, if it makes sense for you.",
                            **BODY_TEXT_STYLE,
                        ),
                    ),
                    padding_left="1.5rem",
                    margin_bottom="2rem",
                ),
                rx.text(
                    "We don't sell VPNs or payment workarounds. We just show you where the prices are different.",
                    color=COLOR_TEXT_SECONDARY,
                    font_style="italic",
                    **BODY_TEXT_STYLE,
                ),
                max_width=MAX_WIDTH,
                margin="0 auto",
                padding=PADDING_SECTION,
            ),
            background=COLOR_BACKGROUND_ALT,
        ),
        
        # What's live right now
        rx.box(
            rx.box(
                rx.heading(
                    "What's live right now",
                    as_="h2",
                    margin_bottom="2rem",
                    **HEADING_LG_STYLE,
                ),
                rx.text(
                    "PriceDuck is in early MVP.",
                    margin_bottom="0.75rem",
                    color=COLOR_TEXT_PRIMARY,
                    **BODY_TEXT_STYLE,
                ),
                rx.text(
                    "We're starting with a small set of services and countries, and we'll keep expanding coverage over time.",
                    margin_bottom="3rem",
                    color=COLOR_TEXT_SECONDARY,
                    **BODY_TEXT_STYLE,
                ),
                
                rx.heading(
                    "Services covered today",
                    as_="h3",
                    margin_bottom="1rem",
                    **HEADING_MD_STYLE,
                ),
                rx.unordered_list(
                    rx.list_item(
                        rx.link(
                            rx.text("Adobe Creative Cloud All Apps"),
                            href=cheapest_slug if cheapest_slug else "#",
                            color=COLOR_BLACK,
                            text_decoration="underline",
                            _hover={"color": COLOR_TEXT_SECONDARY},
                        ),
                    ),
                    padding_left="1.5rem",
                    margin_bottom="3rem",
                    font_size=FONT_SIZE_BASE,
                ),
                
                rx.heading(
                    "Countries and regions",
                    as_="h3",
                    margin_bottom="1rem",
                    **HEADING_MD_STYLE,
                ),
                rx.text(
                    " · ".join([region["name"] for region in UNIQUE_REGIONS]),
                    line_height="1.8",
                    color=COLOR_TEXT_SECONDARY,
                    font_size=FONT_SIZE_BASE,
                ),
                max_width=MAX_WIDTH,
                margin="0 auto",
                padding=PADDING_SECTION,
            ),
        ),
        
        # FAQ
        rx.box(
            rx.box(
                rx.heading(
                    "FAQ",
                    as_="h2",
                    margin_bottom="3rem",
                    **HEADING_LG_STYLE,
                ),
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
        ),
        
        # Footer
        site_footer(),
    )

