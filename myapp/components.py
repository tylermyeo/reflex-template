import reflex as rx
from .design_constants import (
    MAX_WIDTH, COLOR_BORDER, LETTER_SPACING_NORMAL, COLOR_TEXT_MUTED
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
                _hover={"text_decoration": "none"},
            ),
            max_width=MAX_WIDTH,
            margin="0 auto",
            padding="1.5rem 2rem",
        ),
        border_bottom=f"1px solid {COLOR_BORDER}",
    )

def site_footer() -> rx.Component:
    """Centralized footer component used across all pages"""
    return rx.box(
        rx.box(
            rx.text(
                "© 2025 PriceDuck. All rights reserved.",
                font_size="0.875rem",
                color=COLOR_TEXT_MUTED,
            ),
            max_width=MAX_WIDTH,
            margin="0 auto",
            padding="2rem 2rem",
        ),
        border_top=f"1px solid {COLOR_BORDER}",
    )

