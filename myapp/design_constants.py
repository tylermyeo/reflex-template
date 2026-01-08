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

# Layout
MAX_WIDTH = "900px"
PADDING_SECTION = "5rem 2rem"
PADDING_BOX = "2rem"
SPACING_SECTION_GAP = "3rem"
SPACING_ELEMENT_GAP = "1rem"

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
    "letter_spacing": LETTER_SPACING_MEDIUM,
}

HEADING_MD_STYLE = {
    "font_size": FONT_SIZE_MD,
    "font_weight": "800",
}

BODY_TEXT_STYLE = {
    "font_size": FONT_SIZE_BASE,
    "line_height": "1.7",
}

# Button Styles
BUTTON_STYLE = {
    "padding": "1rem 2rem",
    "background": COLOR_BLACK,
    "color": COLOR_WHITE,
    "font_weight": "700",
    "font_size": "1rem",
    "border_radius": "0px",
    "_hover": {"background": COLOR_TEXT_PRIMARY},
    "cursor": "pointer",
    "display": "inline-block",
}
