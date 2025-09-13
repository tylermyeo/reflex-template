"""
Layout components for PriceDuck

This module provides layout components like header, footer, and main layout
that ensure consistent structure and styling across all pages.
"""

import reflex as rx
from .theme import Colors, Typography, Spacing, BorderRadius, Shadows, ZIndex
from .components import container, body_text_small, heading_1, body_text, cta_button, body_text_small

def header(**props) -> rx.Component:
    """Site header with navigation and branding - fixed at top"""
    return rx.box(
        container(
            rx.center(
                # Logo/Brand
                rx.link(
                    rx.heading(
                        "PriceDuck",
                        font_family=Typography.FONT_FAMILY,
                        font_size=Typography.TEXT_2XL,
                        font_weight=Typography.WEIGHT_EXTRABOLD,
                        color=Colors.PRIMARY,
                    ),
                    href="/",
                    text_decoration="none",
                    _hover={"text_decoration": "none"},
                ),
                width="100%",
                padding_y=Spacing.MD,
            )
        ),
        background_color=Colors.LIGHT_GREEN,
        border_bottom=f"2px solid {Colors.PRIMARY}",
        position="static",
        top="0",
        left="0",
        right="0",
        z_index=ZIndex.STICKY,
        box_shadow=Shadows.SM,
        **props
    )

def footer() -> rx.Component:
    """Site footer with links and legal information"""
    return rx.box(
        container(
            rx.vstack(
                # Main footer content
                rx.vstack(
                    # Footer brand
                    rx.heading(
                        "PriceDuck",
                        font_family=Typography.FONT_FAMILY,
                        font_size=Typography.TEXT_2XL,
                        font_weight=Typography.WEIGHT_BOLD,
                        color=Colors.PRIMARY,
                        margin_bottom=Spacing.LG,
                    ),
                    
                    # Navigation section
                    rx.vstack(
                        rx.heading(
                            "Quick Links",
                            font_family=Typography.FONT_FAMILY,
                            font_size=Typography.TEXT_SM,
                            font_weight=Typography.WEIGHT_SEMIBOLD,
                            color=Colors.PRIMARY,
                            margin_bottom=Spacing.SM,
                            text_transform="uppercase",
                            letter_spacing="0.05em",
                        ),
                        
                        # Primary links
                        rx.hstack(
                            rx.link(
                                "Home",
                                href="/",
                                color=Colors.PRIMARY,
                                font_family=Typography.FONT_FAMILY,
                                font_size=Typography.TEXT_SM,
                                _hover={
                                    "color": Colors.PRIMARY_HOVER,
                                    "text_decoration": "underline"
                                }
                            ),
                            rx.link(
                                "About",
                                href="/about",
                                color=Colors.PRIMARY,
                                font_family=Typography.FONT_FAMILY,
                                font_size=Typography.TEXT_SM,
                                _hover={
                                    "color": Colors.PRIMARY_HOVER,
                                    "text_decoration": "underline"
                                }
                            ),
                            rx.link(
                                "Contact",
                                href="mailto:tylermyeo@gmail.com",
                                color=Colors.PRIMARY,
                                font_family=Typography.FONT_FAMILY,
                                font_size=Typography.TEXT_SM,
                                _hover={
                                    "color": Colors.PRIMARY_HOVER,
                                    "text_decoration": "underline"
                                }
                            ),
                            spacing=Spacing.XL,
                            justify="center",
                            wrap="wrap",
                        ),
                        
                        # Legal links
                        rx.hstack(
                            rx.link(
                                "Privacy Policy",
                                href="/privacy",
                                color=Colors.PRIMARY,
                                font_family=Typography.FONT_FAMILY,
                                font_size=Typography.TEXT_SM,
                                _hover={
                                    "color": Colors.PRIMARY_HOVER,
                                    "text_decoration": "underline"
                                }
                            ),
                            rx.link(
                                "Terms of Service",
                                href="/terms",
                                color=Colors.PRIMARY,
                                font_family=Typography.FONT_FAMILY,
                                font_size=Typography.TEXT_SM,
                                _hover={
                                    "color": Colors.PRIMARY_HOVER,
                                    "text_decoration": "underline"
                                }
                            ),
                            spacing=Spacing.XL,
                            justify="center",
                            wrap="wrap",
                            margin_top=Spacing.SM,
                        ),
                        
                        align="center",
                        spacing=Spacing.SM,
                        margin_bottom=Spacing.XXL,
                    ),
                    
                    # Disclaimer section
                    rx.vstack(
                        rx.heading(
                            "Legal",
                            font_family=Typography.FONT_FAMILY,
                            font_size=Typography.TEXT_SM,
                            font_weight=Typography.WEIGHT_SEMIBOLD,
                            color=Colors.PRIMARY,
                            margin_bottom=Spacing.SM,
                            text_transform="uppercase",
                            letter_spacing="0.05em",
                        ),
                        
                        body_text_small(
                            "Disclosure: This website contains affiliate links. We may earn a commission if you make a purchase through these links, at no additional cost to you.",
                            text_align="center",
                            max_width="700px",
                            line_height=Typography.LEADING_RELAXED,
                        ),
                        
                        align="center",
                        margin_bottom=Spacing.XXL,
                    ),
                    
                    align="center",
                    spacing=Spacing.LG,
                ),
                
                # Copyright bar
                rx.divider(
                    color=Colors.GRAY_300,
                    margin_y=Spacing.LG,
                ),
                
                rx.text(
                    "© 2025 PriceDuck. All rights reserved.",
                    font_family=Typography.FONT_FAMILY,
                    font_size=Typography.TEXT_SM,
                    color=Colors.GRAY_500,
                    text_align="center",
                ),
                
                spacing=Spacing.LG,
                align="center",
                width="100%",
            )
        ),
        margin_top=Spacing.XXXXL,
        padding=f"{Spacing.XXXL} 0 {Spacing.XL} 0",
        background_color=Colors.LIGHT_GREEN,
        border_top=f"2px solid {Colors.PRIMARY}",
        width="100%",
    )

def main_layout(*children, **props) -> rx.Component:
    """Main page layout wrapper"""
    return rx.box(
        *children,
        min_height="100vh",
        font_family=Typography.FONT_FAMILY,
        background_color=Colors.PAGE_BACKGROUND,
        **props
    )

def page_wrapper(*children, include_header: bool = True, include_footer: bool = True, **props) -> rx.Component:
    """Complete page wrapper with optional header and footer"""
    components = []
    
    if include_header:
        components.append(header())
    
    # Main content
    components.append(
        rx.box(
            *children,
            flex="1",
            **props
        )
    )
    
    if include_footer:
        components.append(footer())
    
    return main_layout(
        rx.vstack(
            *components,
            spacing="0",
            align="stretch",
            min_height="100vh",
        )
    )

def content_section(*children, **props) -> rx.Component:
    """Content section with consistent spacing"""
    return container(
        rx.vstack(
            *children,
            spacing=Spacing.XL,
            padding_y=Spacing.XXXL,
            **props
        )
    )

def hero_section(*children, **props) -> rx.Component:
    """Hero section with larger spacing and centered content"""
    return rx.box(
        container(
            rx.vstack(
                *children,
                spacing=Spacing.XXL,
                align="center",
                text_align="center",
                **props
            )
        ),
        padding=f"{Spacing.XXXXL} 0",
        background_color=Colors.PAGE_BACKGROUND,
        width="100%",
    ) 

def callout_card(*children, background_color: str = None, border_color: str = None, **props) -> rx.Component:
    """Generic callout card template with customizable background and border colors"""
    default_props = {
        "background_color": background_color or Colors.LIGHT_GREEN,
        "border": f"2px solid {border_color or Colors.PRIMARY}",
        "border_radius": BorderRadius.XXXL,
        "padding": Spacing.XL,
        "max_width": "800px",
        "width": "100%",
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.box(
        rx.vstack(
            *children,
            spacing=Spacing.SM,
            align="center",
        ),
        **default_props
    )

def price_callout_card(title: str, region_name: str, price_display: str, **props) -> rx.Component:
    """Price callout card template with pricing information"""
    return callout_card(
        rx.vstack(
            body_text_small(title, 
                           color=Colors.PRIMARY, 
                           font_weight=Typography.WEIGHT_BOLD,
                           text_transform="uppercase",
                           letter_spacing="0.1em"),
            heading_1(region_name, 
                     color=Colors.PRIMARY,
                     margin_bottom="0",
                     font_size=Typography.TEXT_2XL,
                     text_transform="uppercase",
                     font_weight=Typography.WEIGHT_BOLD),
            heading_1(price_display, 
                     color=Colors.PRIMARY,
                     margin_bottom="0",
                     font_size=Typography.TEXT_5XL),
            body_text("PER MONTH", color=Colors.PRIMARY, font_size=Typography.TEXT_SM),
            rx.link(
                cta_button(
                    "Unlock This Price with NordVPN",
                    size="lg",
                ),
                href="https://go.nordvpn.net/aff_c?offer_id=15&aff_id=120959&url_id=902",
                is_external=True,
                text_decoration="none",
            ),
            body_text_small("UP TO 70% OFF", 
                           color=Colors.PRIMARY, 
                           font_weight=Typography.WEIGHT_BOLD,
                           text_transform="uppercase",
                           letter_spacing="0.1em"),
            spacing=Spacing.SM,
            align="center",
        ),
        **props
    )

def table_callout_card(*children, **props) -> rx.Component:
    """Table callout card template for data tables"""
    return callout_card(
        *children,
        background_color=Colors.LIGHT_PINK,
        border_color=Colors.PRIMARY,
        **props
    )