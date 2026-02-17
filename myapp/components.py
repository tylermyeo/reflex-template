import reflex as rx
from .design_constants import (
    MAX_WIDTH, COLOR_BLACK, COLOR_TEXT_MUTED,
    LETTER_SPACING_NORMAL, SPACING_LG, PADDING_BOX, FONT_SIZE_SM
)

def site_header() -> rx.Component:
    """Centralized header component used across all pages"""
    return rx.box(
        rx.box(
            rx.link(
                rx.heading(
                    "PriceDuck",
                    font_size="1.25rem",
                    font_weight="800",
                    letter_spacing=LETTER_SPACING_NORMAL,
                ),
                href="/",
                text_decoration="none",
                color="inherit",
                _hover={"text_decoration": "none", "opacity": "0.6"},
                transition="opacity 0.15s ease-out",
            ),
            max_width=MAX_WIDTH,
            margin="0 auto",
            padding=f"{SPACING_LG} {PADDING_BOX}",
        ),
        border_bottom=f"1px solid {COLOR_BLACK}",
    )

def site_footer() -> rx.Component:
    """Centralized footer component used across all pages"""
    return rx.box(
        rx.box(
            rx.text(
                "\u00a9 2026 PriceDuck. All rights reserved.",
                font_size=FONT_SIZE_SM,
                color=COLOR_TEXT_MUTED,
            ),
            max_width=MAX_WIDTH,
            margin="0 auto",
            padding=f"{PADDING_BOX} {PADDING_BOX}",
        ),
        border_top=f"1px solid {COLOR_BLACK}",
    )
