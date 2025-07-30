"""
Reusable styled components for PriceDuck

This module provides pre-styled components that use the design tokens
from theme.py to ensure consistency across the application.
"""

import reflex as rx
from .theme import Colors, Typography, Spacing, BorderRadius, Shadows, Animation

# Button variants
def primary_button(text: str, **props) -> rx.Component:
    """Primary button component with brand styling"""
    default_props = {
        "background_color": Colors.PRIMARY,
        "color": Colors.WHITE,
        "font_family": Typography.FONT_FAMILY,
        "font_weight": Typography.WEIGHT_SEMIBOLD,
        "font_size": Typography.TEXT_BASE,
        "padding": f"{Spacing.MD} {Spacing.XL}",
        "border_radius": BorderRadius.LG,
        "border": "none",
        "cursor": "pointer",
        "transition": f"all {Animation.NORMAL} ease-in-out",
        "_hover": {
            "background_color": Colors.PRIMARY_HOVER,
            "transform": "translateY(-1px)",
            "box_shadow": Shadows.HOVER_MD,
        },
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.button(text, **default_props)

def secondary_button(text: str, **props) -> rx.Component:
    """Secondary button component with outline styling"""
    default_props = {
        "background_color": "transparent",
        "color": Colors.PRIMARY,
        "border": f"1px solid {Colors.PRIMARY}",
        "font_family": Typography.FONT_FAMILY,
        "font_weight": Typography.WEIGHT_SEMIBOLD,
        "font_size": Typography.TEXT_BASE,
        "padding": f"{Spacing.MD} {Spacing.XL}",
        "border_radius": BorderRadius.LG,
        "cursor": "pointer",
        "transition": f"all {Animation.NORMAL} ease-in-out",
        "_hover": {
            "background_color": Colors.PRIMARY_LIGHT,
        },
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.button(text, **default_props)

def cta_button(text: str, **props) -> rx.Component:
    """Call-to-action button with purple brand styling (matches existing VPN button)"""
    default_props = {
        "background_color": Colors.PRIMARY,
        "color": Colors.WHITE,
        "font_family": Typography.FONT_FAMILY,
        "font_weight": Typography.WEIGHT_BOLD,
        "font_size": Typography.TEXT_LG,
        "padding": f"{Spacing.LG} {Spacing.XXL}",
        "border_radius": BorderRadius.FULL,
        "border": "none",
        "cursor": "pointer",
        "transition": f"all {Animation.NORMAL} ease-in-out",
        "_hover": {
            "background_color": Colors.PRIMARY + "95",
            "transform": "translateY(-2px)",
            "box_shadow": Shadows.HOVER_MD,
        },
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.button(text, **default_props)

# Typography components
def heading_1(text: str, **props) -> rx.Component:
    """Main page heading (H1)"""
    default_props = {
        "font_family": Typography.FONT_FAMILY,
        "font_size": Typography.TEXT_5XL,
        "font_weight": Typography.WEIGHT_EXTRABOLD,
        "font_style": Typography.FONT_STYLE,
        "font_optical_sizing": Typography.FONT_OPTICAL_SIZING,
        "font_variation_settings": Typography.FONT_VARIATION_SETTINGS,
        "line_height": Typography.LEADING_TIGHT,
        "color": Colors.PRIMARY,
        "margin_bottom": Spacing.LG,
        "as_": "h1",
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.heading(text, **default_props)

def heading_2(text: str, **props) -> rx.Component:
    """Section heading (H2)"""
    default_props = {
        "font_family": Typography.FONT_FAMILY,
        "font_size": Typography.TEXT_2XL,
        "font_weight": Typography.WEIGHT_SEMIBOLD,
        "font_style": Typography.FONT_STYLE,
        "font_optical_sizing": Typography.FONT_OPTICAL_SIZING,
        "font_variation_settings": Typography.FONT_VARIATION_SETTINGS,
        "line_height": Typography.LEADING_TIGHT,
        "color": Colors.PRIMARY,
        "margin_bottom": Spacing.MD,
        "as_": "h2",
        "max_width": "20ch",  # Approximately 4 words (5 chars per word average)
        "text_align": "center",
        "margin_x": "auto",  # Center the block itself
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.heading(text, **default_props)

def heading_3(text: str, **props) -> rx.Component:
    """Sub-section heading (H3)"""
    default_props = {
        "font_family": Typography.FONT_FAMILY,
        "font_size": Typography.TEXT_XL,
        "font_weight": Typography.WEIGHT_SEMIBOLD,
        "font_style": Typography.FONT_STYLE,
        "font_optical_sizing": Typography.FONT_OPTICAL_SIZING,
        "font_variation_settings": Typography.FONT_VARIATION_SETTINGS,
        "line_height": Typography.LEADING_SNUG,
        "color": Colors.GRAY_800,
        "margin_bottom": Spacing.SM,
        "as_": "h3",
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.heading(text, **default_props)

def body_text(text: str, **props) -> rx.Component:
    """Standard body text"""
    default_props = {
        "font_family": Typography.FONT_FAMILY,
        "font_size": Typography.TEXT_BASE,
        "font_style": Typography.FONT_STYLE,
        "font_optical_sizing": Typography.FONT_OPTICAL_SIZING,
        "font_variation_settings": Typography.FONT_VARIATION_SETTINGS,
        "line_height": Typography.LEADING_NORMAL,
        "color": Colors.PRIMARY,
        "font_weight": Typography.WEIGHT_SEMIBOLD,
        "max_width": "45ch",  # Approximately 9 words (5 chars per word average)
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.text(text, **default_props)

def body_text_large(text: str, **props) -> rx.Component:
    """Large body text for emphasis"""
    default_props = {
        "font_family": Typography.FONT_FAMILY,
        "font_size": Typography.TEXT_LG,
        "font_style": Typography.FONT_STYLE,
        "font_optical_sizing": Typography.FONT_OPTICAL_SIZING,
        "font_variation_settings": Typography.FONT_VARIATION_SETTINGS,
        "line_height": Typography.LEADING_RELAXED,
        "color": Colors.PRIMARY,
        "max_width": "50ch",  # Approximately 9 words (larger font)
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.text(text, **default_props)

def body_text_small(text: str, **props) -> rx.Component:
    """Small body text for captions, disclaimers, etc."""
    default_props = {
        "font_family": Typography.FONT_FAMILY,
        "font_size": Typography.TEXT_SM,
        "line_height": Typography.LEADING_NORMAL,
        "color": Colors.GRAY_600,
        "max_width": "40ch",  # Approximately 9 words (smaller font)
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.text(text, **default_props)

# Layout components
def card(*children, **props) -> rx.Component:
    """Card container with shadow and rounded corners"""
    return rx.box(
        *children,
        background_color=Colors.WHITE,
        border_radius=BorderRadius.LG,
        box_shadow=Shadows.DEFAULT,
        padding=Spacing.XL,
        border=f"1px solid {Colors.GRAY_200}",
        **props
    )

def container(*children, **props) -> rx.Component:
    """Main content container with max width and centered alignment"""
    return rx.box(
        *children,
        max_width="1200px",
        margin="0 auto",
        padding_x=Spacing.LG,
        width="100%",
        **props
    )

def section(*children, **props) -> rx.Component:
    """Section wrapper with consistent vertical spacing"""
    return rx.box(
        *children,
        margin_bottom=Spacing.XXXL,
        **props
    )

# Table components
def styled_table(*children, **props) -> rx.Component:
    """Styled table container"""
    return rx.table_container(
        rx.table(
            *children,
            variant="simple",  # Changed from "striped" to "simple" for flat design
            size="lg",
            font_family=Typography.FONT_FAMILY,
        ),
        width="100%",
        overflow_x="auto",
        border_radius=BorderRadius.LG,
        background_color="transparent",  # Make background transparent
        **props
    )

def table_header(*children, **props) -> rx.Component:
    """Styled table header - removed as requested"""
    return rx.thead(
        rx.tr(
            *children,
        ),
        **props
    )

def table_header_cell(text: str, **props) -> rx.Component:
    """Styled table header cell"""
    default_props = {
        "font_weight": Typography.WEIGHT_BOLD,  # Make text one level bolder
        "color": Colors.PRIMARY,  # Use PRIMARY color
        "padding": Spacing.MD,
        "text_align": "left",
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.th(text, **default_props)

def table_cell(content, **props) -> rx.Component:
    """Styled table cell"""
    default_props = {
        "padding": Spacing.MD,
        "color": Colors.PRIMARY,  # Use PRIMARY color
        "font_weight": Typography.WEIGHT_EXTRABOLD,  # Make text bolder
        "font_size": Typography.TEXT_LG,  # Make text bigger
        "border_bottom": f"2px solid {Colors.PRIMARY}",  # Match callout card border thickness and color
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.td(content, **default_props)

# Status and feedback components
def success_text(text: str, **props) -> rx.Component:
    """Success status text"""
    default_props = {
        "color": Colors.SUCCESS,
        "font_family": Typography.FONT_FAMILY,
        "font_weight": Typography.WEIGHT_MEDIUM,
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.text(text, **default_props)

def error_text(text: str, **props) -> rx.Component:
    """Error status text"""
    default_props = {
        "color": Colors.ERROR,
        "font_family": Typography.FONT_FAMILY,
        "font_weight": Typography.WEIGHT_MEDIUM,
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.text(text, **default_props)

def badge(text: str, variant: str = "default", **props) -> rx.Component:
    """Badge component with different variants"""
    variant_styles = {
        "default": {
            "background_color": Colors.GRAY_100,
            "color": Colors.GRAY_700,
        },
        "success": {
            "background_color": Colors.SUCCESS,
            "color": Colors.WHITE,
        },
        "warning": {
            "background_color": Colors.WARNING,
            "color": Colors.WHITE,
        },
        "error": {
            "background_color": Colors.ERROR,
            "color": Colors.WHITE,
        },
    }
    
    styles = variant_styles.get(variant, variant_styles["default"])
    
    return rx.box(
        text,
        font_family=Typography.FONT_FAMILY,
        font_size=Typography.TEXT_XS,
        font_weight=Typography.WEIGHT_MEDIUM,
        padding=f"{Spacing.XS} {Spacing.SM}",
        border_radius=BorderRadius.FULL,
        display="inline-block",
        **styles,
        **props
    ) 