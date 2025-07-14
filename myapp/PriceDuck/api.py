import os
import json
import gspread
import pandas as pd
import cachetools
from google.oauth2.service_account import Credentials

# Create a TTLCache that stores up to 100 items and expires them after 24 hours
data_cache = cachetools.TTLCache(maxsize=100, ttl=86400)

# Function to load data from Google Sheets
def load_sheet_data():
    """Load and cache data from Google Sheets."""
    if 'sheet_data' in data_cache:
        return data_cache['sheet_data']
    
    try:
        # First check if we have the credentials as a JSON string
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            try:
                creds_info = json.loads(creds_json)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in GOOGLE_CREDENTIALS_JSON secret")
        else:
            # Fall back to file-based credentials
            creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
            if not creds_path:
                raise ValueError("Neither GOOGLE_CREDENTIALS_JSON nor GOOGLE_CREDENTIALS_PATH secret is set")
            
            # Read the credentials from the JSON file
            try:
                with open(creds_path, 'r') as f:
                    creds_info = json.load(f)
            except FileNotFoundError:
                raise ValueError(f"Google credentials file not found at {creds_path}")
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in Google credentials file at {creds_path}")
            except Exception as e:
                raise ValueError(f"Error reading credentials file: {str(e)}")

        SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]

        creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        gc = gspread.authorize(creds)
        
        # Open the Google Sheet
        SHEET_NAME = "Global Pricing"
        try:
            spreadsheet = gc.open(SHEET_NAME)
        except Exception as e:
            raise ValueError(f"Could not open sheet '{SHEET_NAME}': {str(e)}")
        
        worksheet = spreadsheet.sheet1  # Select the first worksheet
        data = worksheet.get_all_records()
        
        if not data:
            raise ValueError("No data found in the Google Sheet")

        df = pd.DataFrame(data)
        
        # Validate required columns
        required_columns = ["Product", "Region Name", "Amount", "Currency", "Timestamp"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns in sheet: {', '.join(missing_columns)}")
        
        # Convert Amount to numeric, replacing errors with NaN
        df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
        
        # Convert Timestamp to datetime, replacing errors with NaN
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        
        # Remove rows with invalid data
        df = df.dropna(subset=["Amount", "Timestamp"])
        
        data_cache['sheet_data'] = df
        return df
    except Exception as e:
        raise ValueError(f"Error loading sheet data: {str(e)}")

# Set empty initial data to avoid build-time errors
initial_df = pd.DataFrame()
initial_products = []
initial_selected_product = ""
initial_conversion_rates = {"USD": 1.0}