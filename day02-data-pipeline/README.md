# Day 2 — NSE Data Pipeline v1

Part of my **30-day public build** of an event-driven quant trading model on NSE stocks.

---

## What this is

To study how stocks react to earnings events, I needed two things:
- **Price data** — what the stock actually did
- **Event data** — when the announcement hit, from the official source

This script connects both. It fetches official quarterly earnings dates directly from NSE's corporate announcements API and aligns them with historical OHLCV price data from Yahoo Finance.

---

## What I was trying to build

```
NSE corporate API → earnings dates
         +
Yahoo Finance → historical prices
         ↓
merged dataset with EarningsFlag column
         ↓
foundation for event-study analysis
```

---

## What actually happened

The code ran clean. No errors. Processed all 5 stocks.

Found **0 earnings events** across every single one.

NSE's API was silently rejecting every request — returning an empty response instead of JSON. The cookie session was dying between calls and the code just moved on quietly instead of flagging it.

This is documented in the output:
```
Fetching official NSE announcements for RELIANCE...
  ↳ Network or JSON parsing error for RELIANCE: Expecting value: line 1 column 1 (char 0)
Successfully processed RELIANCE

Found 0 corporate announcement dates on the price charts.
```

---

## Known problems in this version

**1. Filter too narrow**
Only catches `"Quarterly Results"` — NSE also uses `"Financial Results"`, `"Unaudited Financial Results"` etc. A lot of valid events get silently dropped.

**2. No after-hours handling**
If NSE releases results at 6 PM after market close, the flag lands on the wrong date. The market can't react until next morning. This makes every return window built on top of it measure the wrong thing.

**3. Cookie session doesn't survive the loop**
By the time the second stock runs, the NSE session from the first call is already dead. Need to refresh cookies per symbol, not once at the start.

---

## Stack

| Tool | Why |
|------|-----|
| `curl_cffi` | Mimics Chrome's TLS fingerprint — NSE blocks standard requests |
| `yfinance` | Historical OHLCV price data — reliable and clean |
| `pandas` | Data structuring and date alignment |

Install:
```bash
pip install curl_cffi yfinance pandas
```

---

## How to run

```bash
python day2_pipeline.py
```

Expected output right now: prices load fine, 0 earnings events flagged. That's the bug this day is documenting.

---

## What's next

Day 3 covers what happened when I kept fighting the NSE API across 4 versions — and why I eventually stopped.

Day 4 is where the pivot happens.

Follow the full build → [LinkedIn](https://www.linkedin.com/in/your-profile) | [GitHub](https://github.com/your-username/event-driven-quant)

---

*Building an event-driven quant model from scratch, entirely in public. 30 days. Every mistake documented.*
