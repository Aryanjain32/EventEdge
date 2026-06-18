# Day 4 — First Event-Outcome DataFrame
#
# After 3 days of fighting NSE's API, I stopped and asked a different question.
# Not "how do I collect this data reliably?"
# But "what am I actually trying to study?"
#
# The answer: does the market react to information in a predictable way?
#
# To study that I needed two things:
#   1. A list of earnings events with dates — built using Perplexity (quarterly_reports.csv)
#   2. What the stock actually did after each event — fetched from yfinance
#
# This script builds the first version of that event-outcome table.
# No NIFTY benchmark yet. No relative strength. Just the raw event rows
# with return windows attached — enough to start asking outcome questions.

import yfinance as yf
import pandas as pd

# Earnings event dates — 10 NIFTY50 stocks, 2021-2025
# Built using Perplexity as a research tool to unblock the pipeline
# while the NSE API issue gets resolved separately
qr_dates = pd.read_csv("quarterly_reports.csv")

# Map CSV symbols to yfinance format
# Note: CSV uses 'RELI' for Reliance — yfinance needs 'RELIANCE.NS'
symbol_map = {
    "RELI":       "RELIANCE.NS",
    "HDFCBANK":   "HDFCBANK.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "SBIN":       "SBIN.NS",
    "ICICIBANK":  "ICICIBANK.NS",
    "INFY":       "INFY.NS",
    "LICI":       "LICI.NS",
    "SUNPHARMA":  "SUNPHARMA.NS",
    "MARUTI":     "MARUTI.NS",
    "HCLTECH":    "HCLTECH.NS",
}

qr_dates['symbol'] = qr_dates['symbol'].astype(str).str.strip().str.upper()
qr_dates['announcement_date'] = pd.to_datetime(qr_dates['announcement_date']).dt.date
qr_dates = qr_dates.dropna(subset=['announcement_date'])

final_feature_rows = []

for csv_symbol, yf_ticker in symbol_map.items():
    price_df = yf.download(yf_ticker, start='2021-01-01', end='2025-12-31', progress=False)

    if price_df.empty:
        print(f"No data for {yf_ticker}")
        continue

    if isinstance(price_df.columns, pd.MultiIndex):
        price_df.columns = price_df.columns.get_level_values(0)

    price_df = price_df.reset_index()
    price_df['Date'] = pd.to_datetime(price_df['Date']).dt.date
    price_df = price_df.sort_values('Date')

    # What happened after each earnings event?
    # GapPct   — overnight gap at next open (immediate shock)
    # Return1D — full day return on first trading session after event
    # Return3D — return 3 sessions later (does the reaction hold or reverse?)
    price_df['GapPct']   = (price_df['Open'].shift(-1) - price_df['Close']) / price_df['Close']
    price_df['Return1D'] = (price_df['Close'].shift(-1) - price_df['Close']) / price_df['Close']
    price_df['Return3D'] = (price_df['Close'].shift(-3) - price_df['Close']) / price_df['Close']

    stock_events = qr_dates[qr_dates['symbol'] == csv_symbol]['announcement_date'].tolist()

    for event_date in stock_events:
        # Announcement may come after market close — map to next trading session
        future_days = price_df[price_df['Date'] >= event_date]

        if not future_days.empty:
            row = future_days.iloc[0].copy()
            row['Ticker'] = yf_ticker
            row['EventDate'] = event_date
            final_feature_rows.append(row)

# First event-outcome table — one row per earnings event
events_df = pd.DataFrame(final_feature_rows)
output_cols = ['Ticker', 'EventDate', 'Date', 'Close', 'GapPct', 'Return1D', 'Return3D']
events_df = events_df[output_cols].dropna()

print(f"\n=== Event-Outcome DataFrame ===")
print(f"Total events mapped: {len(events_df)}")
print(f"Stocks covered: {events_df['Ticker'].nunique()}")
print()
print(events_df.head(10).to_string())
