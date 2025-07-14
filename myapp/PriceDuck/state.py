import reflex as rx
import pandas as pd
import plotly.graph_objects as go
from sqlmodel import Session, select
from .database import engine, ProductPrice

class State(rx.State):
    """The app state."""
    products: list[str] = []
    selected_product: str = "Creative Cloud All Apps"
    data_load_error: str = ""

    def on_load(self):
        self.fetch_products()

    def fetch_products(self):
        try:
            with Session(engine) as session:
                statement = select(ProductPrice)
                all_prices = session.exec(statement).all()
                product_names = sorted(list(set(p.Product for p in all_prices)))
                self.products = product_names
                if self.products and "Creative Cloud All Apps" not in self.products:
                    self.products.insert(0, "Creative Cloud All Apps")
                self.selected_product = "Creative Cloud All Apps"
        except Exception as e:
            self.data_load_error = f"Could not load products from database. Have you synced the data? Error: {e}"

    @rx.var
    def product_data(self) -> list[dict]:
        if not self.selected_product:
            return []
        try:
            with Session(engine) as session:
                statement = select(ProductPrice).where(ProductPrice.Product == self.selected_product).order_by(ProductPrice.Amount)
                results = session.exec(statement).all()
                return [row.dict() for row in results]
        except Exception:
            return [] 