# Day 4 — Stopping Was the Right Move

Code from Day 4 of building EventEdge, an event-driven quant model for NSE stocks, in public.

3 days of fighting NSE's API. On Day 4, I stopped.

Not because I gave up — because I realized I'd been asking the wrong question for 3 days.

The question I kept asking: how do I collect this data reliably?
The question I should have been asking: what am I actually trying to study?

One of those questions builds infrastructure forever. The other one builds a research model.

---

## The shift

I had been treating data collection as the project.

It was never the project.

The project is: does the market react to information in a predictable way?

To study that, I needed two things:
1. A list of earnings events with exact dates
2. What the stock actually did after each event

For (1), instead of spending another day fighting NSE's API, I used Perplexity to research and structure the earnings dates directly into a clean CSV — 10 NIFTY50 stocks, 2021 to 2025, 160 events total. That's `quarterly_reports.csv` in this folder.

For (2), yfinance handles price data cleanly with no bot issues.

---

## What this script builds

One row per earnings event per stock — an event-outcome table.

```
Ticker      EventDate     Date          Close    GapPct    Return1D    Return3D
INFY.NS     2021-07-12    2021-07-12    1377.3   0.0055    -0.0019      0.0213
INFY.NS     2021-10-11    2021-10-11    1504.6   -0.0082   -0.0034      0.0147
...
```

Three outcome columns:
- `GapPct` — overnight gap at next open. The market's immediate reaction to the news.
- `Return1D` — full session return on the first trading day after the event.
- `Return3D` — return 3 sessions later. Does the reaction hold, or does it reverse?

No NIFTY benchmark yet. No relative strength. That comes in Day 5.
This is just the foundation — events mapped to outcomes, clean enough to analyze.

---

## How to run it

```bash
pip install yfinance pandas

python event_outcome.py
```

`quarterly_reports.csv` must be in the same folder.

---

## Files

```
day04-event-outcome/
├── event_outcome.py        # loads CSV, fetches prices, builds event-outcome table
├── quarterly_reports.csv   # 160 earnings events, 10 NIFTY50 stocks, 2021-2025
└── README.md
```

---

## What comes next

Day 5 — adding the NIFTY benchmark and relative strength features to this table.
A stock +2% on an event day means something different depending on whether NIFTY was up 3% or down 2% that same day.

#QuantFinance #AlgoTrading #Python #BuildingInPublic
