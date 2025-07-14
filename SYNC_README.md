# Google Sheets Sync Setup

This sync script fetches pricing data from your Google Sheets and saves it as JSON for the app to use.

## Setup Instructions

### 1. Get your Spreadsheet ID
From your Google Sheets URL:
```
https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]/edit
```

### 2. Set up Google Service Account (Option A - Recommended)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Sheets API
4. Create a Service Account:
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Download the JSON key file
   - Save it as `service_account.json` in your project root

5. Share your Google Sheet with the service account email (found in the JSON file)

### 3. Set up Environment Variables (Option B)

Instead of a file, you can use environment variables:

```bash
# Option 1: JSON string
export GOOGLE_CREDENTIALS_JSON='{"type":"service_account","project_id":"..."}'

# Option 2: File path
export GOOGLE_CREDENTIALS_PATH="/path/to/your/service_account.json"

# Your spreadsheet ID
export GOOGLE_SHEET_ID="your_spreadsheet_id_here"

# Exchange rate API key (optional - for currency conversion)
export EXCHANGE_API_KEY="your_exchange_rate_api_key"
```

### 4. Google Sheets Format

Your sheet should be named "Global Pricing" with these columns:
- **Product** (e.g., "Creative Cloud All Apps")
- **Region** (e.g., "TR", "US", "IN")
- **Region Name** (e.g., "Turkey", "United States", "India")
- **Currency** (e.g., "USD")
- **Amount** (e.g., 12.99)
- **Period** (e.g., "monthly")
- **Page Link** (e.g., "https://adobe.com/tr")
- **Timestamp** (e.g., "2025-01-08")

## Usage

### Run the sync script:
```bash
python sync_data.py
```

This will:
1. Try to connect to your Google Sheet
2. Fetch live currency exchange rates (if API key provided)
3. Convert all prices to USD for consistent comparison
4. If successful: Download data and save to `myapp/data/pricing.json`
5. If failed: Create fallback data and show error message

### Currency Conversion

The script automatically converts all prices to USD using live exchange rates from [exchangerate-api.com](https://exchangerate-api.com/). 

To enable currency conversion:
1. Sign up for a free API key at exchangerate-api.com
2. Set the environment variable: `export EXCHANGE_API_KEY="your_api_key"`

Without the API key, only USD prices will be processed (others will be skipped).

### The app will automatically use the JSON data

The Reflex app loads the JSON file and displays it in the table, sorted by price (cheapest first).

## Troubleshooting

**404 Error**: Check your spreadsheet ID and make sure the sheet is shared with your service account email.

**Permission Error**: Make sure your service account has "Viewer" access to the Google Sheet.

**Sheet Not Found**: Ensure your worksheet is named exactly "Global Pricing".

**No Credentials**: The script will create fallback data if no credentials are found.

## Manual Updates

You can also manually edit `myapp/data/pricing.json` if needed. The app will automatically use the updated data. 