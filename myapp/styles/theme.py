"""
Central design system for PriceDuck

This module contains all design tokens (colors, typography, spacing, etc.)
that should be used consistently across the application.
"""

# Color palette
class Colors:
    # Primary brand colors - Purple theme to match existing button
    PRIMARY = "#6366F1"  # Indigo
    PRIMARY_HOVER = "#4F46E5"
    PRIMARY_LIGHT = "#E0E7FF"
    
    # Secondary colors - Purple to match existing VPN button
    SECONDARY = "#8B5CF6"  # Purple (matches existing button color_scheme="purple")
    SECONDARY_HOVER = "#7C3AED"
    ACCENT = "#10B981"     # Emerald for success/highlights
    
    # Neutral colors
    WHITE = "#FFFFFF"
    GRAY_50 = "#F9FAFB"
    GRAY_100 = "#F3F4F6"
    GRAY_200 = "#E5E7EB"
    GRAY_300 = "#D1D5DB"
    GRAY_400 = "#9CA3AF"
    GRAY_500 = "#6B7280"
    GRAY_600 = "#4B5563"
    GRAY_700 = "#374151"
    GRAY_800 = "#1F2937"
    GRAY_900 = "#111827"
    BLACK = "#000000"
    
    # Status colors
    SUCCESS = "#10B981"    # Green for cheapest prices
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#3B82F6"
    
    # Brand specific
    BRAND_PRIMARY = "#8B5CF6"  # Purple for brand consistency

# Typography
class Typography:
    # Font families
    FONT_FAMILY = "'Bricolage Grotesque', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    FONT_MONO = "'JetBrains Mono', 'SF Mono', 'Consolas', monospace"
    
    # Font sizes (rem units for scalability)
    TEXT_XS = "0.75rem"     # 12px
    TEXT_SM = "0.875rem"    # 14px
    TEXT_BASE = "1rem"      # 16px
    TEXT_LG = "1.125rem"    # 18px
    TEXT_XL = "1.25rem"     # 20px
    TEXT_2XL = "1.5rem"     # 24px
    TEXT_3XL = "1.875rem"   # 30px
    TEXT_4XL = "2.25rem"    # 36px
    TEXT_5XL = "3rem"       # 48px
    
    # Font weights
    WEIGHT_LIGHT = "200"
    WEIGHT_NORMAL = "400"
    WEIGHT_MEDIUM = "500" 
    WEIGHT_SEMIBOLD = "600"
    WEIGHT_BOLD = "700"
    WEIGHT_EXTRABOLD = "800"
    
    # Bricolage Grotesque specific properties
    FONT_OPTICAL_SIZING = "auto"
    FONT_VARIATION_SETTINGS = "'wdth' 100"
    FONT_STYLE = "normal"
    
    # Line heights
    LEADING_TIGHT = "1.25"
    LEADING_SNUG = "1.375"
    LEADING_NORMAL = "1.5"
    LEADING_RELAXED = "1.625"
    LEADING_LOOSE = "2"

# Spacing system (using rem for scalability)
class Spacing:
    NONE = "0"
    XS = "0.25rem"   # 4px
    SM = "0.5rem"    # 8px
    MD = "1rem"      # 16px
    LG = "1.5rem"    # 24px
    XL = "2rem"      # 32px
    XXL = "3rem"     # 48px
    XXXL = "4rem"    # 64px
    XXXXL = "6rem"   # 96px

# Border radius
class BorderRadius:
    NONE = "0"
    SM = "0.125rem"   # 2px
    DEFAULT = "0.25rem"  # 4px
    MD = "0.375rem"   # 6px
    LG = "0.5rem"     # 8px - matches existing button border_radius="0.5em"
    XL = "0.75rem"    # 12px
    XXL = "1rem"      # 16px
    XXXL = "1.5rem"   # 24px
    FULL = "9999px"

# Box shadows
class Shadows:
    NONE = "none"
    SM = "0 1px 2px 0 rgb(0 0 0 / 0.05)"
    DEFAULT = "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)"
    MD = "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)"
    LG = "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)"
    XL = "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)"
    XXL = "0 25px 50px -12px rgb(0 0 0 / 0.25)"
    INNER = "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)"
    
    # Hover shadows for interactive elements
    HOVER_SM = "0 2px 4px 0 rgb(0 0 0 / 0.1)"
    HOVER_MD = "0 4px 12px rgba(107,99,246,0.3)"  # Matches existing button hover

# Z-index scale
class ZIndex:
    DROPDOWN = "1000"
    STICKY = "1020"
    FIXED = "1030"
    MODAL_BACKDROP = "1040"
    MODAL = "1050"
    POPOVER = "1060"
    TOOLTIP = "1070"
    
# Breakpoints for responsive design
class Breakpoints:
    SM = "640px"
    MD = "768px"
    LG = "1024px"
    XL = "1280px"
    XXL = "1536px"

# Animation durations
class Animation:
    FAST = "0.1s"
    NORMAL = "0.2s"
    SLOW = "0.3s"
    SLOWER = "0.5s" 