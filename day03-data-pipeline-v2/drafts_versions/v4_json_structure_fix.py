import pandas as pd
import yfinance as yf
from datetime import datetime
from curl_cffi import requests 

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/companies-listing/corporate-filings-announcements'
}

def get_announcements(symbol, years=5):
    session = requests.Session(impersonate="chrome")
    try:
        # Step 1: Collect structural cookies from the main filings directory page
        session.get("https://www.nseindia.com/companies-listing/corporate-filings-announcements", headers=HEADERS, timeout=10)
        
        # Step 2: Grab the JSON data structure
        url = f"https://www.nseindia.com/api/corporate-announcements?symbol={symbol}"
        r = session.get(url, headers=HEADERS, timeout=10)
        
        if r.status_code != 200:
            print(f"  ↳ NSE Blocked Endpoint (HTTP Status {r.status_code})")
            return pd.DataFrame()
            
        raw_json = r.json()
        
        # CRUCIAL FIX: NSE wraps data arrays inside the dictionary key labeled 'rows'
        data_list = []
        if isinstance(raw_json, list):
            data_list = raw_json
        elif isinstance(raw_json, dict):
            if "rows" in raw_json:
                data_list = raw_json["rows"]
            elif "data" in raw_json:
                data_list = raw_json["data"]
                
        print(f"  ↳ Total raw announcements received from NSE for {symbol}: {len(data_list)}")
        
    except Exception as e:
        print(f"  ↳ Connection failed for {symbol}: {e}")
        return pd.DataFrame()

    if not data_list:
        return pd.DataFrame()

    valid_records = []
    for item in data_list:
        # Normalize the strings to upper case to remove case variations
        subject = str(item.get("subject", "")).upper()
        desc = str(item.get("desc", "")).upper()
        
        # Catch all common combinations of financial result descriptions
        if any(keyword in subject or keyword in desc for keyword in ["QUARTERLY", "FINANCIAL RESULT", "FINANCIALS", "EARNING"]):
            
            # Extract timestamps matching corporate dissemination fields
            potential_date = None
            for key in ["attchblddate", "an_dt", "dt", "p_dt", "date"]:
                if key in item and item[key]:
                    potential_date = item[key]
                    break
            
            if potential_date:
                valid_records.append({
                    "symbol": item.get("symbol", symbol),
                    "subject": item.get("subject", "Financial Results"),
                    "raw_date_string": potential_date
                })

    df = pd.DataFrame(valid_records)
    print(f"  ↳ Filtered down to {len(df)} financial/earnings records.")

    if not df.empty:
        # Standardize date objects cleanly
        df["date"] = pd.to_datetime(df["raw_date_string"], errors="coerce")
        df = df.dropna(subset=["date"])
        
        cutoff = pd.Timestamp.today() - pd.DateOffset(years=years)
        df = df[df["date"] >= cutoff]
        return df[["symbol", "subject", "date"]]
        
    return pd.DataFrame()


def merge_price_with_earnings(symbol, yf_symbol, start="2020-01-01", end="2026-01-01"):
    prices = yf.download(yf_symbol, start=start, end=end, progress=False)
    
    if prices.empty:
        raise ValueError(f"No price data loaded from Yahoo for {yf_symbol}")
        
    if isinstance(prices.columns, pd.MultiIndex):
        prices.columns = prices.columns.get_level_values(0)

    # Initialize all rows to False
    prices['EarningsFlag'] = False

    print(f"Processing official NSE data stream for {symbol}...")
    announcements_df = get_announcements(symbol)
    
    if announcements_df.empty:
        print(f"  ↳ Warning: No parsed corporate matches found for {symbol}.")
        return prices

    # Clean local indices to timezone-naive formats
    prices.index = pd.to_datetime(prices.index).tz_localize(None)
    announcement_dates = pd.to_datetime(announcements_df["date"]).dt.tz_localize(None)

    matched_count = 0
    for announce_date in announcement_dates:
        # Handle calendar adjustments (roll forward to next available market hour entry)
        future_trading_days = prices.index[prices.index >= announce_date]
        if not future_trading_days.empty:
            actual_trading_day = future_trading_days[0]
            prices.at[actual_trading_day, 'EarningsFlag'] = True
            matched_count += 1

    print(f"  ↳ Successfully flagged {matched_count} dates on the chart vector.")
    return prices


# Execution Area
nifty50 = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS"
}

combined_data = {}
for nse_symbol, yf_symbol in nifty50.items():
    try:
        df = merge_price_with_earnings(nse_symbol, yf_symbol)
        combined_data[nse_symbol] = df
        print(f"Completed processing for {nse_symbol}\n")
    except Exception as e:
        print(f"Error handling loops for {nse_symbol}: {e}\n")

# Output Verification View
if "RELIANCE" in combined_data:
    r_df = combined_data["RELIANCE"]
    earnings_days = r_df[r_df['EarningsFlag'] == True]
    
    if not earnings_days.empty:
        print("--- Verified Output Rows ---")
        print(earnings_days[["Open", "High", "Low", "Close", "EarningsFlag"]].head())
    else:
        print("--- Structural Fallback Notice ---")
        print("Matches still hit zero. Here are the column listings present in your dataframe structure:")
        print(r_df.columns.tolist())
        print(r_df.head(2))