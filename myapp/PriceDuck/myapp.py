# Welcome to Reflex! This file outlines the steps to create a basic app

import reflex as rx
from .pages import index, health, not_found
from .state import State

# Add state and page to the app.
app = rx.App(state=State)
app.add_page(index)
app.add_page(health, route="/health")

# Add 404 page
not_found_text = "The page you were looking for could not be found"
app.add_custom_404_page(
    title="404 - Page Not Found",
    description=not_found_text,
    component=not_found(not_found_text)
)
