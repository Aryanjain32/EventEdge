import pandas as pd
import yfinance as yf
from datetime import datetime
from curl_cffi import requests 

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/'
}

def get_announcements(symbol, years=5):
    session = requests.Session(impersonate="chrome")
    try:
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        url = f"https://www.nseindia.com/api/corporate-announcements?symbol={symbol}"
        r = session.get(url, headers=HEADERS, timeout=10)
        
        if r.status_code != 200:
            return pd.DataFrame(columns=["symbol", "subject", "date"])
            
        data = r.json()
    except Exception as e:
        print(f"  ↳ Network/API Error for {symbol}: {e}")
        return pd.DataFrame(columns=["symbol", "subject", "date"])

    # Filter to only capture Quarterly Results filings
    results = [item for item in data if "Quarterly Results" in item.get("subject", "")]
    df = pd.DataFrame(results)

    if not df.empty:
        # Crucial fix: Parse the entire timestamp string cleanly
        df["date"] = pd.to_datetime(df["dt"], errors="coerce")
        cutoff = pd.Timestamp.today() - pd.DateOffset(years=years)
        df = df[df["date"] >= cutoff]
        return df[["symbol", "subject", "date"]]
    else:
        return pd.DataFrame(columns=["symbol", "subject", "date"])


def merge_price_with_earnings(symbol, yf_symbol, start="2020-01-01", end="2026-01-01"):
    prices = yf.download(yf_symbol, start=start, end=end, progress=False)
    
    if prices.empty:
        raise ValueError(f"No price data returned for {yf_symbol}")
        
    if isinstance(prices.columns, pd.MultiIndex):
        prices.columns = prices.columns.get_level_values(0)

    # Initialize the earnings flag to False for all days
    prices['EarningsFlag'] = False

    # Pull the exact corporate event dates from the official NSE API
    print(f"Fetching official NSE announcements for {symbol}...")
    announcements_df = get_announcements(symbol)
    
    if announcements_df.empty:
        print(f"  ↳ No corporate announcements found on NSE for {symbol}.")
        return prices

    # Clean price index to timezone-naive timestamps for accurate calculations
    prices.index = pd.to_datetime(prices.index).tz_localize(None)
    announcement_dates = pd.to_datetime(announcements_df["date"]).dt.tz_localize(None)

    # Smart Matching Loop: Finds the exact trading session that absorbed the news
    matched_count = 0
    for announce_date in announcement_dates:
        # Find trading days that are greater than or equal to the announcement timestamp
        future_trading_days = prices.index[prices.index >= announce_date]
        
        if not future_trading_days.empty:
            # The very first available trading day in that list is our market match
            actual_trading_day = future_trading_days[0]
            prices.at[actual_trading_day, 'EarningsFlag'] = True
            matched_count += 1

    print(f"  ↳ Aligned {matched_count} announcements to active market sessions.")
    return prices


# Execution Block
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
        print(f"Successfully processed {nse_symbol}\n")
    except Exception as e:
        print(f"Error processing {nse_symbol}: {e}\n")

# Access and show structural preview 
if "RELIANCE" in combined_data:
    print("--- Aligned NSE Earnings Match (Reliance Preview) ---")
    earnings_days = combined_data["RELIANCE"][combined_data["RELIANCE"]['EarningsFlag'] == True]
    print(earnings_days[["Open", "High", "Low", "Close", "Volume", "EarningsFlag"]].head())