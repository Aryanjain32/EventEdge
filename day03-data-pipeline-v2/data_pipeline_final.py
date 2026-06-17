import io
import pandas as pd
import yfinance as yf
from datetime import datetime
from curl_cffi import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.nseindia.com/companies-listing/corporate-filings-announcements'
}

def fetch_master_nse_announcements(years=5):
    """
    Downloads the entire recent historical corporate announcements database 
    from the NSE master CSV export endpoint in a single query.
    """
    print("Connecting to NSE to download master corporate filings directory...")
    session = requests.Session(impersonate="chrome")
    
    try:
        # Step 1: Establish real-user cookie session on the entry board
        session.get("https://www.nseindia.com/companies-listing/corporate-filings-announcements", headers=HEADERS, timeout=15)
        
        # Step 2: Request the massive compiled database dump directly via CSV export
        csv_url = "https://www.nseindia.com/api/corporate-announcements?index=equities&csv=true"
        response = session.get(csv_url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"  ↳ Master CSV download rejected by NSE (Status Code: {response.status_code})")
            return pd.DataFrame()
            
        # Parse text string into Pandas dataframe structure
        csv_data = response.content.decode('utf-8-sig', errors='ignore')
        df = pd.read_csv(io.StringIO(csv_data))
        print(f"  ↳ Successfully parsed {len(df)} total corporate records across all NSE listings.")
        
        # Clean down the column naming spaces if present
        df.columns = df.columns.str.strip().str.upper()
        
        # Look for standard dates column mappings
        date_col = None
        for col in ['BROADCAST DATE/TIME', 'BROADCAST DATE', 'DATE', 'AN_DT']:
            if col in df.columns:
                date_col = col
                break
                
        if not date_col:
            print("  ↳ Could not find valid date headers in the master registry dump.")
            return pd.DataFrame()
            
        df['PARSED_DATE'] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=['PARSED_DATE'])
        
        # Slice off anything outside the historical range window
        cutoff = pd.Timestamp.today() - pd.DateOffset(years=years)
        df = df[df['PARSED_DATE'] >= cutoff]
        
        return df

    except Exception as e:
        print(f"  ↳ Failed to download or process master list: {e}")
        return pd.DataFrame()


def merge_price_with_earnings(symbol, yf_symbol, master_announcements_df, start="2020-01-01", end="2026-01-01"):
    """Loads historical prices and slices the locally stored master table for flags"""
    prices = yf.download(yf_symbol, start=start, end=end, progress=False)
    
    if prices.empty:
        raise ValueError(f"No price data loaded from Yahoo for {yf_symbol}")
        
    if isinstance(prices.columns, pd.MultiIndex):
        prices.columns = prices.columns.get_level_values(0)

    prices['EarningsFlag'] = False
    prices.index = pd.to_datetime(prices.index).tz_localize(None)

    if master_announcements_df.empty:
        return prices

    # Filter out company records just for this specific symbol loop locally
    company_mask = (master_announcements_df['SYMBOL'].astype(str).str.strip().str.upper() == symbol.upper())
    company_df = master_announcements_df[company_mask]
    
    # Isolate financial result entries strictly
    results_mask = company_df['SUBJECT'].astype(str).str.upper().str.contains('QUARTERLY|FINANCIAL RESULT|FINANCIALS|EARNING', na=False)
    earnings_df = company_df[results_mask]

    if earnings_df.empty:
        print(f"  ↳ No historical quarterly filings noted for {symbol} within the active slice.")
        return prices

    # Match timeframes up to the active financial sessions
    announcement_dates = earnings_df['PARSED_DATE'].dt.tz_localize(None)
    matched_count = 0
    
    for announce_date in announcement_dates:
        future_trading_days = prices.index[prices.index >= announce_date]
        if not future_trading_days.empty:
            actual_trading_day = future_trading_days[0]
            prices.at[actual_trading_day, 'EarningsFlag'] = True
            matched_count += 1

    print(f"  ↳ Aligned {matched_count} official corporate filings with your stock chart index.")
    return prices


# Main Loop Area
nifty50 = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "HDFCBANK": "HDFCBANK.NS"
}

# Fetch the entire stock exchange filing record pool ONCE
master_df = fetch_master_nse_announcements(years=5)

combined_data = {}
for nse_symbol, yf_symbol in nifty50.items():
    try:
        print(f"Processing calculations for {nse_symbol}...")
        df = merge_price_with_earnings(nse_symbol, yf_symbol, master_df)
        combined_data[nse_symbol] = df
        print(f"Completed mapping data metrics for {nse_symbol}.\n")
    except Exception as e:
        print(f"Error handling math transformations for {nse_symbol}: {e}\n")

# Verify structural outputs match 
if "RELIANCE" in combined_data:
    r_df = combined_data["RELIANCE"]
    earnings_days = r_df[r_df['EarningsFlag'] == True]
    
    if not earnings_days.empty:
        print("\n=== Verified Output Rows ===")
        print(earnings_days[["Open", "High", "Low", "Close", "EarningsFlag"]].head())
    else:
        print("\n=== Data Mismatch Notice ===")
        print("Prices generated cleanly but flags remained unassigned. Sample price rows:")
        print(r_df[["Open", "Close", "EarningsFlag"]].head(3))