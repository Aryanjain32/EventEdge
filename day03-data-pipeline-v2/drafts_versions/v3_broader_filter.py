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
        # Crucial: Visit the filings portal page to get specialized session cookies
        session.get("https://www.nseindia.com/companies-listing/corporate-filings-announcements", headers=HEADERS, timeout=10)
        
        # Pull data from the endpoint
        url = f"https://www.nseindia.com/api/corporate-announcements?symbol={symbol}"
        r = session.get(url, headers=HEADERS, timeout=10)
        
        if r.status_code != 200:
            print(f"  ↳ NSE Endpoint returned status code {r.status_code}")
            return pd.DataFrame()
            
        data = r.json()
        
        # If the response is wrapped inside a dictionary like {"data": [...]}
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
            
    except Exception as e:
        print(f"  ↳ Connection failed for {symbol}: {e}")
        return pd.DataFrame()

    if not data or not isinstance(data, list):
        print(f"  ↳ No list data found in response for {symbol}")
        return pd.DataFrame()

    # Filter to look for Financial results or Board Meetings discussing results
    valid_records = []
    for item in data:
        subject = str(item.get("subject", "")).upper()
        desc = str(item.get("desc", "")).upper()
        
        # Broaden filter text slightly to catch alternative phrasing like 'Financial Results'
        if "QUARTERLY" in subject or "FINANCIAL RESULTS" in subject or "QUARTERLY" in desc:
            
            # FAIL-SAFE: Check every known naming key used by NSE for timestamps
            potential_date = None
            for key in ["attchblddate", "an_dt", "dt", "p_dt", "date"]:
                if key in item and item[key]:
                    potential_date = item[key]
                    break
            
            if potential_date:
                valid_records.append({
                    "symbol": item.get("symbol", symbol),
                    "subject": item.get("subject", "Quarterly Results"),
                    "raw_date_string": potential_date
                })

    df = pd.DataFrame(valid_records)

    if not df.empty:
        # Parse the raw date text flexibly
        df["date"] = pd.to_datetime(df["raw_date_string"], errors="coerce")
        # Drop rows where the date couldn't parse
        df = df.dropna(subset=["date"])
        
        # Filter out anything older than your cutoff range
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

    prices['EarningsFlag'] = False

    print(f"Fetching structural NSE data for {symbol}...")
    announcements_df = get_announcements(symbol)
    
    if announcements_df.empty:
        print(f"  ↳ Warning: 0 filtered records returned by the NSE parser for {symbol}.")
        return prices

    # Match timezone boundaries
    prices.index = pd.to_datetime(prices.index).tz_localize(None)
    announcement_dates = pd.to_datetime(announcements_df["date"]).dt.tz_localize(None)

    matched_count = 0
    for announce_date in announcement_dates:
        # Map the exact announcement time directly forward to the next open trading block
        future_trading_days = prices.index[prices.index >= announce_date]
        if not future_trading_days.empty:
            actual_trading_day = future_trading_days[0]
            prices.at[actual_trading_day, 'EarningsFlag'] = True
            matched_count += 1

    print(f"  ↳ Successfully pinned {matched_count} announcements onto chart timelines.")
    return prices


# Execution Context
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
        print(f"Finished processing {nse_symbol}\n")
    except Exception as e:
        print(f"Error handling loops for {nse_symbol}: {e}\n")

# Verify structural population
if "RELIANCE" in combined_data:
    r_df = combined_data["RELIANCE"]
    earnings_days = r_df[r_df['EarningsFlag'] == True]
    
    if not earnings_days.empty:
        print("--- Verified Output Rows ---")
        print(earnings_days[["Open", "High", "Low", "Close", "EarningsFlag"]].head())
    else:
        print("--- Fallback Notice ---")
        print("No matches hit. Here is the head of your standard chart data:")
        print(r_df[["Open", "Close", "EarningsFlag"]].head())