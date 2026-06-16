# v1 — First Attempt: Basic curl_cffi with per-symbol API calls
#
# What I tried: curl_cffi with Chrome impersonation, calling NSE once per symbol.
# What broke: pd.to_datetime() was receiving timestamps like "01-APR-2023 18:45:00"
#             which it parsed as .date() objects (date only, no time).
#             When comparing against the price index (which has full timestamps),
#             the isin() check failed silently — 0 matches every time.
#
# Lesson: Always inspect raw API response field types before parsing dates.

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
            print(f"  ↳ NSE blocked request for {symbol} (Status Code: {r.status_code})")
            return pd.DataFrame(columns=["symbol", "subject", "date"])
            
        data = r.json()
    except Exception as e:
        print(f"  ↳ Network or JSON parsing error for {symbol}: {e}")
        return pd.DataFrame(columns=["symbol", "subject", "date"])

    results = [item for item in data if "Quarterly Results" in item.get("subject", "")]
    df = pd.DataFrame(results)

    if not df.empty:
        # BUG: .dt.date strips the time component, making isin() fail later
        df["date"] = pd.to_datetime(df["dt"], errors="coerce").dt.date
        cutoff = (pd.Timestamp.today() - pd.DateOffset(years=years)).date()
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

    print(f"Fetching official NSE announcements for {symbol}...")
    announcements_df = get_announcements(symbol)
    earning_dates = announcements_df["date"].tolist()

    prices.index = pd.to_datetime(prices.index).date
    
    # BUG: This comparison silently returns 0 matches because of the date type mismatch above
    prices['EarningsFlag'] = prices.index.isin(earning_dates)
    return prices


nifty50 = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "INFY": "INFY.NS",
    "ICICIBANK": "ICICIBANK.NS"
}

combined_data = {}
for nse_symbol, yf_symbol in nifty50.items():
    try:
        df = merge_price_with_earnings(nse_symbol, yf_symbol)
        combined_data[nse_symbol] = df
        print(f"Successfully processed {nse_symbol}\n")
    except Exception as e:
        print(f"Error processing {nse_symbol}: {e}\n")

if "RELIANCE" in combined_data:
    print("--- Official NSE Earnings Match (Reliance Preview) ---")
    print(combined_data["RELIANCE"].head())
    nse_flagged_days = combined_data["RELIANCE"][combined_data["RELIANCE"]['EarningsFlag'] == True]
    print(f"\nFound {len(nse_flagged_days)} corporate announcement dates on the price charts.")
    print(nse_flagged_days.head())
