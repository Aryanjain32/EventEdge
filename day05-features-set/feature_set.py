# Day 5 — Adding Market Context to Every Event
# Same earnings report, two stocks, two different market moments,
# and the reaction was nothing alike.
# A positive surprise during a bull run gets aggressive buying.
# The same surprise during a panic phase barely moves the stock.
# The event is identical. The market around it isn't.
# That's why this script brings NIFTY into the picture and adds
# relative strength on top of the base event features.

import yfinance as yf
import pandas as pd

nifty50 = [
    "RELIANCE.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "BHARTIARTL.NS",
    "SBIN.NS",
    "ICICIBANK.NS",
    "LICI.NS",
    "SUNPHARMA.NS",
    "MARUTI.NS",
    "HCLTECH.NS",
]

qr_dates = pd.read_csv("quarterly_reports.csv")

qr_dates['symbol'] = qr_dates['symbol'].astype(str).str.strip().str.upper()
qr_dates['announcement_date']=pd.to_datetime(qr_dates['announcement_date']).dt.date
qr_dates = qr_dates.dropna(subset=['announcement_date'])
final_feature_rows=[]

for ticker in nifty50:
    price_df=yf.download(ticker,start='2021-01-01',end='2025-12-31')

    if isinstance(price_df.columns,pd.MultiIndex):
        price_df.columns=price_df.columns.get_level_values(0)
 
    price_df=price_df.reset_index()
    price_df['Date']=pd.to_datetime(price_df['Date']).dt.date
    price_df = price_df.sort_values('Date')
    
    #Feature_building

    #FEATURE 1: 5-Day Trend before today
    prev_close=price_df['Close'].shift(1)
    close_5_days_ago=price_df['Close'].shift(6)
    price_df['PreEventReturn']=(prev_close-close_5_days_ago)/close_5_days_ago
    
    # FEATURE 2: Next day's opening gap shock reaction
    price_df['GapPct'] = (price_df['Open'].shift(-1) - price_df['Close']) / price_df['Close']
        
    # FEATURE 3: Next day's closing price immediate reaction
    price_df['Return1D'] = (price_df['Close'].shift(-1) - price_df['Close']) / price_df['Close']
        
    # FEATURE 4: 3 days later closing price continuation behavior
    price_df['Return3D'] = (price_df['Close'].shift(-3) - price_df['Close']) / price_df['Close']
        
    # FEATURE 5: Volume Spike (Today's Volume divided by 20-day average volume)
    avg_vol_20d = price_df['Volume'].rolling(window=20).mean()
    price_df['VolumeRatio'] = price_df['Volume'] / avg_vol_20d
    
    clean_csv_name = ticker.replace(".NS", "").strip().upper()

    stock_announcements=qr_dates[qr_dates['symbol']==clean_csv_name]['announcement_date'].tolist()
    
    #4. Map the earnings dates to our calculated table
    for earning_date in stock_announcements:
        # Find trading days on or right after the announcement date
        future_trading_days = price_df[price_df['Date'] >= earning_date]
        
        if not future_trading_days.empty:
            # Grab the very first available trading day row
            event_day_row = future_trading_days.iloc[0].copy()
            event_day_row['Ticker'] = ticker
            
                # Save this calculated row into our final list
            final_feature_rows.append(event_day_row)
# STEP 3: Combine Rows into the Final Dataset ---
features_df = pd.DataFrame(final_feature_rows)

# Keep only your core feature columns for a clean view
output_columns = ['Ticker', 'Date', 'Close', 'PreEventReturn', 'GapPct', 'Return1D', 'Return3D', 'VolumeRatio']
features_df = features_df[output_columns].dropna()

print("\n=== Processing Complete! ===")
print(features_df.head(10))
nifty=yf.download(tickers='^NSEI',start='2021-01-01',end='2025-12-31')

if isinstance (nifty.columns,pd.MultiIndex):
   nifty.columns=nifty.columns.get_level_values(0)

nifty=nifty.reset_index()
nifty['Date']=pd.to_datetime(nifty['Date']).dt.date
nifty=nifty.sort_values('Date')

nifty['Nifty1D_Return']=nifty['Close'].pct_change()

nifty_prev_close=nifty['Close'].shift(1)
nifty_close_5_days_ago=nifty['Close'].shift(6)
nifty['Nifty5D_Return']=(nifty_prev_close-nifty_close_5_days_ago)/nifty_close_5_days_ago
# Keep only the benchmark columns we need for the merge
nifty_benchmarks=nifty[['Date','Nifty1D_Return','Nifty5D_Return']]

# --- STEP 6: Merge NIFTY Benchmarks into your Features DataFrame ---
features_df=pd.merge(features_df,nifty_benchmarks,on='Date',how='left')

# --- STEP 7: Calculate Relative Stock Strength ---
features_df['RelativeStrength5D'] = features_df['PreEventReturn'] - features_df['Nifty5D_Return']

 # Feature 7: 1-Day Post-Event Relative Strength (The Alpha Trigger)
features_df['RelativeStrength1D'] = features_df['Return1D'] - features_df['Nifty1D_Return']


 # Clean up column sorting layout
final_columns = [
     'Ticker', 'Date', 'Close', 
     'PreEventReturn', 'Nifty5D_Return', 'RelativeStrength5D',  # 5-Day pre-event trend block
     'GapPct', 
     'Return1D', 'Nifty1D_Return', 'RelativeStrength1D',        # 1-Day post-event reaction block
     'Return3D', 'VolumeRatio',
 ]
features_df = features_df[final_columns].dropna()
    
features_df['Target3D']=(features_df['Return3D']>0).astype(int)

print(features_df.head(10))

# #QuantFinance #AlgoTrading #Python #BuildingInPublic
