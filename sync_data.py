#!/usr/bin/env python3
"""
Sync script to fetch pricing data from Google Sheets and save as JSON.
This allows the app to use static JSON data while keeping data updates simple.
"""

import gspread
import json
import os
from google.auth import load_credentials_from_file
from google.oauth2.service_account import Credentials

def load_sheet_data():
    """Load data from Google Sheets using service account credentials"""
    
    # Try to load credentials from environment or file
    credentials = None
    
    # Method 1: Try JSON string from environment variable
    if os.getenv('GOOGLE_CREDENTIALS_JSON'):
        try:
            import json
            creds_info = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
            credentials = Credentials.from_service_account_info(
                creds_info,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        except Exception as e:
            print(f"Error loading credentials from JSON env var: {e}")
    
    # Method 2: Try file path from environment variable
    if not credentials and os.getenv('GOOGLE_CREDENTIALS_PATH'):
        try:
            credentials = Credentials.from_service_account_file(
                os.getenv('GOOGLE_CREDENTIALS_PATH'),
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        except Exception as e:
            print(f"Error loading credentials from file: {e}")
    
    # Method 3: Try default credential files
    if not credentials:
        for filename in ['credentials.json', 'service_account.json']:
            try:
                credentials = Credentials.from_service_account_file(
                    filename,
                    scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
                )
                print(f"✅ Loaded credentials from {filename}")
                break
            except Exception as e:
                print(f"Tried {filename}: {e}")
                continue
    
    if not credentials:
        raise Exception("No valid Google credentials found. Please set GOOGLE_CREDENTIALS_JSON or GOOGLE_CREDENTIALS_PATH environment variable, or add service_account.json file.")
    
    try:
        # Initialize the client
        gc = gspread.authorize(credentials)
        
        # Your spreadsheet ID
        SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID', '1M4awqqkU8EVHiT8sGxPxD3DW6aIyoj1mHuAHqqVyQhs')
        
        # Open the spreadsheet
        sheet = gc.open_by_key(SPREADSHEET_ID)
        
        # Get the "Scraped Pricing" worksheet
        worksheet = sheet.worksheet("Scraped Pricing")
        
        # Get all records (assumes first row has headers)
        records = worksheet.get_all_records()
        
        print(f"Successfully loaded {len(records)} records from Google Sheets")
        return records
        
    except Exception as e:
        print(f"Error accessing Google Sheets: {e}")
        raise

def save_to_json(data, filename="myapp/data/pricing.json"):
    """Save data to JSON file"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Sort by amount (cheapest first)
    sorted_data = sorted(data, key=lambda x: float(x.get('Amount', 0)))
    
    # Convert to the format expected by the app
    formatted_data = []
    for item in sorted_data:
        formatted_item = {
            "product": item.get('Product', 'Creative Cloud All Apps'),
            "region": item.get('Region', ''),
            "region_name": item.get('Region Name', ''),
            "currency": item.get('Currency', 'USD'),
            "amount": float(item.get('Amount', 0)),
            "period": item.get('Period', 'monthly'),
            "page_link": item.get('Page Link', ''),
            "timestamp": item.get('Timestamp', '')
        }
        formatted_data.append(formatted_item)
    
    with open(filename, 'w') as f:
        json.dump(formatted_data, f, indent=2)
    
    print(f"Data saved to {filename}")
    return formatted_data

def create_fallback_data():
    """Create fallback data if Google Sheets is not available"""
    fallback_data = [
        {
            "product": "Creative Cloud All Apps",
            "region": "TR",
            "region_name": "Turkey",
            "currency": "USD",
            "amount": 12.99,
            "period": "monthly",
            "page_link": "https://adobe.com/tr",
            "timestamp": "2025-01-08"
        },
        {
            "product": "Creative Cloud All Apps",
            "region": "IN",
            "region_name": "India",
            "currency": "USD",
            "amount": 15.99,
            "period": "monthly",
            "page_link": "https://adobe.com/in",
            "timestamp": "2025-01-08"
        },
        {
            "product": "Creative Cloud All Apps",
            "region": "BR",
            "region_name": "Brazil",
            "currency": "USD",
            "amount": 19.99,
            "period": "monthly",
            "page_link": "https://adobe.com/br",
            "timestamp": "2025-01-08"
        },
        {
            "product": "Creative Cloud All Apps",
            "region": "MX",
            "region_name": "Mexico",
            "currency": "USD",
            "amount": 24.99,
            "period": "monthly",
            "page_link": "https://adobe.com/mx",
            "timestamp": "2025-01-08"
        },
        {
            "product": "Creative Cloud All Apps",
            "region": "US",
            "region_name": "United States",
            "currency": "USD",
            "amount": 59.99,
            "period": "monthly",
            "page_link": "https://adobe.com/us",
            "timestamp": "2025-01-08"
        }
    ]
    
    # Save fallback data directly without processing through save_to_json
    # since it's already in the right format
    os.makedirs("myapp/data", exist_ok=True)
    with open("myapp/data/pricing.json", 'w') as f:
        json.dump(fallback_data, f, indent=2)
    print("Data saved to myapp/data/pricing.json")
    print("Created fallback data")
    return fallback_data

def main():
    """Main sync function"""
    print("Starting data sync from Google Sheets...")
    
    try:
        # Try to load from Google Sheets
        sheet_data = load_sheet_data()
        data = save_to_json(sheet_data)
        print(f"✅ Successfully synced {len(data)} records from Google Sheets")
        
    except Exception as e:
        print(f"❌ Error syncing from Google Sheets: {e}")
        print("Creating fallback data instead...")
        data = create_fallback_data()
        print(f"✅ Created fallback data with {len(data)} records")
    
    # Print summary
    print("\n📊 Data Summary:")
    for item in data[:5]:  # Show first 5 items
        print(f"  {item['region_name']}: ${item['amount']:.2f}")
    if len(data) > 5:
        print(f"  ... and {len(data) - 5} more")

if __name__ == "__main__":
    main() 