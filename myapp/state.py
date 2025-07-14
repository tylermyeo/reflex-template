import reflex as rx
import pandas as pd
from .api import load_sheet_data

class State(rx.State):
    """The app state."""
    sheet_data: pd.DataFrame = pd.DataFrame()
    products: list[str] = []
    selected_product: str = "Creative Cloud All Apps"
    data_load_error: str = ""

    def on_load(self):
        self.fetch_data()

    def fetch_data(self):
        self.data_load_error = ""
        try:
            self.sheet_data = load_sheet_data()
            if not self.sheet_data.empty:
                self.products = sorted(list(self.sheet_data["Product"].unique()))
                if "Creative Cloud All Apps" not in self.products:
                    self.products.insert(0, "Creative Cloud All Apps")
                self.selected_product = "Creative Cloud All Apps"
        except Exception as e:
            self.data_load_error = f"Failed to load pricing data. Please ensure credentials are set. Error: {e}"

    @rx.var
    def product_data(self) -> list[dict]:
        if self.sheet_data.empty or not self.selected_product:
            return []
        
        product_df = self.sheet_data[self.sheet_data["Product"] == self.selected_product]
        product_df = product_df.sort_values(by="Amount", ascending=True)
        
        return product_df.to_dict("records") 