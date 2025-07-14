# PriceDuck Design System

A centralized, scalable design system for consistent UI across the PriceDuck application.

## 🎨 Structure

```
myapp/styles/
├── __init__.py      # Central exports
├── theme.py         # Design tokens (colors, fonts, spacing)
├── components.py    # Reusable styled components
├── layout.py        # Layout components (headers, footers, wrappers)
└── README.md        # This documentation
```

## 🏷️ Design Tokens

### Colors
```python
from .styles import Colors

Colors.PRIMARY           # #6366F1 (Indigo)
Colors.SECONDARY        # #8B5CF6 (Purple - brand color)
Colors.SUCCESS          # #10B981 (Green)
Colors.GRAY_700         # #374151 (Text)
Colors.WHITE            # #FFFFFF
```

### Typography
```python
from .styles import Typography

Typography.FONT_FAMILY       # Inter font
Typography.TEXT_4XL          # 2.25rem (36px) - H1
Typography.TEXT_2XL          # 1.5rem (24px) - H2
Typography.TEXT_BASE         # 1rem (16px) - Body
Typography.WEIGHT_BOLD       # 700
Typography.WEIGHT_SEMIBOLD   # 600
```

### Spacing
```python
from .styles import Spacing

Spacing.SM     # 0.5rem (8px)
Spacing.MD     # 1rem (16px)
Spacing.LG     # 1.5rem (24px)
Spacing.XL     # 2rem (32px)
Spacing.XXL    # 3rem (48px)
Spacing.XXXL   # 4rem (64px)
```

## 🧩 Components

### Typography
```python
from .styles import heading_1, heading_2, heading_3, body_text

heading_1("Main Page Title")
heading_2("Section Title")
heading_3("Subsection Title")
body_text("Regular paragraph text")
body_text_large("Emphasized text")
body_text_small("Caption or disclaimer text")
```

### Buttons
```python
from .styles import primary_button, secondary_button, cta_button

primary_button("Primary Action")
secondary_button("Secondary Action")
cta_button("Call to Action")  # Purple brand button
```

### Layout
```python
from .styles import card, container, section

card(
    body_text("Content in a card"),
    button("Action")
)

container(
    # Centers content with max-width
)

section(
    # Adds consistent vertical spacing
)
```

### Page Layout
```python
from .styles import page_wrapper, hero_section, content_section

def my_page():
    return page_wrapper(
        hero_section(
            heading_1("Hero Title"),
            body_text_large("Hero subtitle"),
        ),
        content_section(
            card(
                body_text("Main content")
            )
        )
    )
```

### Tables
```python
from .styles import styled_table, table_header, table_header_cell, table_cell

styled_table(
    table_header(
        table_header_cell("Column 1"),
        table_header_cell("Column 2"),
    ),
    rx.tbody(
        rx.tr(
            table_cell("Data 1"),
            table_cell("Data 2"),
        )
    )
)
```

### Status & Feedback
```python
from .styles import success_text, error_text, badge

success_text("Success message")
error_text("Error message")
badge("Status", variant="success")  # success, warning, error, default
```

## ✅ Best Practices

### 1. Always Use Design System Components
❌ **Don't:**
```python
rx.heading("Title", font_size="2em", color="gray.900")
```

✅ **Do:**
```python
heading_1("Title")
```

### 2. Use Theme Tokens for Custom Styling
❌ **Don't:**
```python
rx.box(background_color="#8B5CF6")
```

✅ **Do:**
```python
rx.box(background_color=Colors.SECONDARY)
```

### 3. Override Props Safely
✅ **Correct way to override:**
```python
heading_1("Title", color=Colors.PRIMARY)  # Will override default color
body_text("Text", font_size=Typography.TEXT_LG)  # Will override default size
```

### 4. Use Layout Components
❌ **Don't:**
```python
rx.vstack(
    rx.heading("Title"),
    rx.text("Content"),
    padding="2rem",
    max_width="1200px",
    margin="0 auto"
)
```

✅ **Do:**
```python
content_section(
    heading_1("Title"),
    body_text("Content")
)
```

## 🚀 Adding New Components

When adding new styled components, follow this pattern:

```python
def my_component(text: str, **props) -> rx.Component:
    """Component description"""
    default_props = {
        "font_family": Typography.FONT_FAMILY,
        "color": Colors.GRAY_700,
        # ... other defaults
    }
    # Allow props to override defaults
    default_props.update(props)
    return rx.text(text, **default_props)
```

## 🎯 Customization

### Change Brand Colors
Edit `theme.py`:
```python
class Colors:
    PRIMARY = "#your-new-primary"
    SECONDARY = "#your-new-secondary"
```

### Add New Spacing
Edit `theme.py`:
```python
class Spacing:
    CUSTOM = "5rem"  # 80px
```

### Modify Typography
Edit `theme.py`:
```python
class Typography:
    FONT_FAMILY = "'Your Font', sans-serif"
```

## 🔍 Troubleshooting

**Prop conflicts?** Make sure components use the safe prop merging pattern.
**Styles not applying?** Check that you're importing from `.styles` not directly from files.
**Inconsistent spacing?** Use `Spacing` tokens instead of hardcoded values.

---

**Remember:** Consistency is key! Always use the design system components and tokens for a professional, maintainable application. 