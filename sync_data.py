#!/usr/bin/env python3
"""
Sync script to fetch pricing data from Google Sheets and save as JSON.
This allows the app to use static JSON data while keeping data updates simple.
"""

import gspread
import json
import os
import requests
from google.auth import load_credentials_from_file
from google.oauth2.service_account import Credentials

# Global cache for conversion rates
conversion_rates_cache = {}

def fetch_conversion_rates():
    """Fetch and cache the latest currency conversion rates with USD as base"""
    global conversion_rates_cache
    
    # Return cached rates if available
    if conversion_rates_cache:
        print("Using cached conversion rates")
        return conversion_rates_cache
    
    try:
        # Get API key from environment
        api_key = os.getenv("EXCHANGE_API_KEY")
        if not api_key:
            print("⚠️  Warning: Missing EXCHANGE_API_KEY environment variable")
            print("   Currency conversion will be skipped")
            return {"USD": 1.0}
            
        print("🔄 Fetching latest currency conversion rates...")
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        rates = data.get("conversion_rates", {})
        
        if not rates:
            raise ValueError("No conversion rates returned from API")
        
        # Cache the rates
        conversion_rates_cache = rates
        print(f"✅ Fetched conversion rates for {len(rates)} currencies")
        return rates
        
    except requests.RequestException as e:
        print(f"❌ Error fetching exchange rates: {e}")
        return {"USD": 1.0}
    except Exception as e:
        print(f"❌ Unexpected error fetching exchange rates: {e}")
        return {"USD": 1.0}

def convert_to_usd(amount, from_currency, conversion_rates):
    """Convert an amount from the given currency to USD"""
    try:
        if not amount or not isinstance(amount, (int, float)):
            return None
            
        # If already USD, return as-is
        if from_currency == "USD":
            return round(float(amount), 2)
            
        # Get conversion rate (rate shows how many units of from_currency = 1 USD)
        from_rate = conversion_rates.get(from_currency)
        
        if not from_rate:
            print(f"⚠️  Warning: No conversion rate found for {from_currency}")
            return None
            
        # Convert to USD: amount in foreign currency / rate = USD amount
        usd_amount = float(amount) / from_rate
        return round(usd_amount, 2)
        
    except (TypeError, ValueError, ZeroDivisionError) as e:
        print(f"❌ Error converting {amount} {from_currency} to USD: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error in currency conversion: {e}")
        return None

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
    """Save data to JSON file with currency conversion"""
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Fetch conversion rates
    print("\n💱 Starting currency conversion...")
    conversion_rates = fetch_conversion_rates()
    
    # Convert to the format expected by the app with USD conversion
    formatted_data = []
    conversion_stats = {"converted": 0, "skipped": 0, "errors": 0}
    
    for item in data:
        try:
            original_amount = item.get('Amount', 0)
            original_currency = item.get('Currency', 'USD')
            
            # Convert to USD
            usd_amount = convert_to_usd(original_amount, original_currency, conversion_rates)
            
            if usd_amount is None:
                conversion_stats["errors"] += 1
                continue  # Skip items that couldn't be converted
            
            formatted_item = {
                "product": item.get('Product', 'Creative Cloud All Apps'),
                "region": item.get('Region', ''),
                "region_name": item.get('Region Name', ''),
                "currency": "USD",  # All prices are now in USD
                "original_currency": original_currency,  # Keep track of original
                "original_amount": float(original_amount),  # Keep original for reference
                "amount": usd_amount,  # USD converted amount
                "period": item.get('Period', 'monthly'),
                "page_link": item.get('Page Link', ''),
                "timestamp": item.get('Timestamp', ''),
                "conversion_rate": conversion_rates.get(original_currency, 1.0)
            }
            formatted_data.append(formatted_item)
            
            if original_currency != "USD":
                conversion_stats["converted"] += 1
            else:
                conversion_stats["skipped"] += 1
                
        except Exception as e:
            print(f"❌ Error processing item: {e}")
            conversion_stats["errors"] += 1
            continue
    
    # Sort by USD amount (cheapest first)
    formatted_data.sort(key=lambda x: x.get('amount', 0))
    
    with open(filename, 'w') as f:
        json.dump(formatted_data, f, indent=2)
    
    print(f"💱 Currency conversion complete:")
    print(f"   ✅ Converted: {conversion_stats['converted']} records")
    print(f"   ⏭️  USD already: {conversion_stats['skipped']} records") 
    print(f"   ❌ Errors: {conversion_stats['errors']} records")
    print(f"📄 Data saved to {filename}")
    
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