import pandas as pd
import yfinance as yf
from datetime import datetime

# NSE blocks normal requests so we use curl_cffi to mimic a real Chrome browser
# took me a while to figure this out - requests just returns nothing without this
from curl_cffi import requests 

# headers that match what Chrome actually sends when you visit a website
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/'
}

def get_announcements(symbol, years=5):
    # impersonate="chrome" matches the TLS fingerprint of a real browser
    # without this NSE silently rejects the request
    session = requests.Session(impersonate="chrome")
    
    try:
        # you have to hit the homepage first to collect cookies
        # NSE won't give you API access without them
        session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
        
        # actual corporate announcements endpoint
        url = f"https://www.nseindia.com/api/corporate-announcements?symbol={symbol}"
        r = session.get(url, headers=HEADERS, timeout=10)
        
        if r.status_code != 200:
            print(f"  ↳ NSE blocked request for {symbol} (Status Code: {r.status_code})")
            return pd.DataFrame(columns=["symbol", "subject", "date"])
            
        data = r.json()

    except Exception as e:
        print(f"  ↳ Network or JSON parsing error for {symbol}: {e}")
        return pd.DataFrame(columns=["symbol", "subject", "date"])

    # filtering for quarterly results only
    # problem i found later - NSE isn't consistent with naming
    # some say "Financial Results", some say "Unaudited Results" - this misses those
    results = [item for item in data if "Quarterly Results" in item.get("subject", "")]
    df = pd.DataFrame(results)

    if not df.empty:
        df["date"] = pd.to_datetime(df["dt"], errors="coerce").dt.date
        cutoff = (pd.Timestamp.today() - pd.DateOffset(years=years)).date()
        df = df[df["date"] >= cutoff]
        return df[["symbol", "subject", "date"]]
    else:
        return pd.DataFrame(columns=["symbol", "subject", "date"])


def merge_price_with_earnings(symbol, yf_symbol, start="2020-01-01", end="2026-01-01"):
    # yahoo finance for prices - this part actually works cleanly
    prices = yf.download(yf_symbol, start=start, end=end, progress=False)
    
    if prices.empty:
        raise ValueError(f"No price data returned for {yf_symbol}")
        
    # yfinance sometimes returns multiindex columns depending on version
    if isinstance(prices.columns, pd.MultiIndex):
        prices.columns = prices.columns.get_level_values(0)

    print(f"Fetching official NSE announcements for {symbol}...")
    announcements_df = get_announcements(symbol)
    earning_dates = announcements_df["date"].tolist()

    # stripping time from index so dates match properly
    prices.index = pd.to_datetime(prices.index).date
    
    # flagging days where an earnings event happened
    # note: this doesn't account for after-hours announcements yet
    # if NSE drops results at 6pm, the market reacts NEXT session not this one
    prices['EarningsFlag'] = prices.index.isin(earning_dates)
    return prices


# nifty 50 sample - nse symbol mapped to yahoo finance format
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

# preview output
if "RELIANCE" in combined_data:
    print("--- Official NSE Earnings Match (Reliance Preview) ---")
    print(combined_data["RELIANCE"].head())
    
    nse_flagged_days = combined_data["RELIANCE"][combined_data["RELIANCE"]['EarningsFlag'] == True]
    print(f"\nFound {len(nse_flagged_days)} corporate announcement dates on the price charts.")
    print(nse_flagged_days.head())
