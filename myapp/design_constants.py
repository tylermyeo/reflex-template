# Typography Scale
FONT_SIZE_XL = "3.5rem"       # Hero headings (h1)
FONT_SIZE_LG = "2.5rem"       # Section headings (h2)
FONT_SIZE_MD = "1.5rem"       # Subsection headings (h3)
FONT_SIZE_BASE = "1.125rem"   # Body text
FONT_SIZE_SM = "0.875rem"     # Small text, footer

# Letter Spacing
LETTER_SPACING_TIGHT = "-0.03em"
LETTER_SPACING_MEDIUM = "-0.025em"
LETTER_SPACING_NORMAL = "-0.02em"

# Colors
COLOR_TEXT_PRIMARY = "#374151"
COLOR_TEXT_SECONDARY = "#6B7280"
COLOR_TEXT_MUTED = "#9CA3AF"
COLOR_BORDER = "#E5E7EB"
COLOR_BACKGROUND_ALT = "#F9FAFB"
COLOR_BLACK = "#000000"
COLOR_WHITE = "#FFFFFF"

# Spacing Scale
SPACING_XS = "0.5rem"
SPACING_SM = "0.75rem"
SPACING_MD = "1rem"
SPACING_LG = "1.5rem"
SPACING_XL = "2rem"
SPACING_2XL = "3rem"

# Layout
MAX_WIDTH = "900px"
PADDING_SECTION = "5rem 2rem"
PADDING_BOX = "2rem"
SPACING_SECTION_GAP = SPACING_2XL
SPACING_ELEMENT_GAP = SPACING_MD

# Typography Styles (Combined Props)
HEADING_XL_STYLE = {
    "font_size": FONT_SIZE_XL,
    "font_weight": "800",
    "line_height": "1.1",
    "letter_spacing": LETTER_SPACING_TIGHT,
}

HEADING_LG_STYLE = {
    "font_size": FONT_SIZE_LG,
    "font_weight": "800",
    "line_height": "1.15",
    "letter_spacing": LETTER_SPACING_MEDIUM,
}

HEADING_MD_STYLE = {
    "font_size": FONT_SIZE_MD,
    "font_weight": "800",
    "line_height": "1.3",
}

BODY_TEXT_STYLE = {
    "font_size": FONT_SIZE_BASE,
    "font_weight": "500",
    "line_height": "1.7",
}

# Button Styles
BUTTON_STYLE = {
    "padding": f"{SPACING_MD} {SPACING_XL}",
    "background": COLOR_BLACK,
    "color": COLOR_WHITE,
    "font_weight": "700",
    "font_size": "1rem",
    "border_radius": "0px",
    "transition": "all 0.15s ease-out",
    "_hover": {
        "background": COLOR_WHITE,
        "color": COLOR_BLACK,
        "box_shadow": f"inset 0 0 0 2px {COLOR_BLACK}",
    },
    "cursor": "pointer",
    "display": "inline-block",
}

# Link Styles
LINK_STYLE = {
    "color": COLOR_BLACK,
    "text_decoration": "underline",
    "_hover": {"color": COLOR_TEXT_SECONDARY},
}

# Step Number Styles (for CMS page instructions)
STEP_NUMBER_STYLE = {
    "font_weight": "800",
    "font_size": FONT_SIZE_MD,
    "color": COLOR_BLACK,
    "margin_bottom": SPACING_XS,
}

# Callout Box Styles (for price cards on CMS pages)
CALLOUT_BOX_STYLE = {
    "background": COLOR_BACKGROUND_ALT,
    "padding": PADDING_BOX,
    "width": "100%",
}
