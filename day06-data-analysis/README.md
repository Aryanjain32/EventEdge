# Day 6 — Letting the Data Push Back

Code from Day 6 of building EventEdge, an event-driven quant model for NSE stocks, in public.

5 days of building. No real findings yet.

Day 6 was the day I stopped building and started actually looking at what the data was saying.

High volume after earnings = strong continuation. That's what I assumed walking in. The data said the opposite.

---

## What this script does

Continues directly from the `features_df` built on Day 5. Runs four stats questions, then visualizes each result to check if it actually holds up.

---

## The four findings

**Finding 1 — Positive earnings gaps don't immediately reverse.**
I expected mean reversion. The data showed mild continuation instead.
Average 3-day return after a positive earnings gap: **+0.38%**
Not a trading edge on its own. But a direction. The market seems to need extra time to fully absorb the information rather than overshooting and snapping back.

**Finding 2 — Bigger gaps don't produce bigger returns.**
Scatter plot of gap size vs 3-day return: pure noise. No diagonal, no relationship.
A stock jumping 5% after earnings wasn't more likely to continue than one jumping 1%. Magnitude alone tells you almost nothing.

**Finding 3 — High volume actually underperformed.**
This was the result that surprised me most. High-volume earnings events produced weaker average follow-through than normal-volume ones.
One possible read: when everyone rushes in immediately after the news, the buying pressure is already exhausted by the time you'd act on it. The information gets priced in too fast for there to be anything left to capture.

**Finding 4 — Relative strength was the strongest signal in the whole dataset.**
Stocks already outperforming NIFTY before the announcement averaged a meaningfully stronger 3-day return than stocks that were underperforming going in.
The market was already signaling strength before the event happened. Strong stocks stayed strong. Weak stocks didn't suddenly become leaders just because of one announcement.

---

## The uncomfortable part

Plotted the cumulative return curve across all events. It wasn't a clean upward line.

Long stretches of struggle. Sharp drawdowns. Recovery. Then setbacks again.

That raised a new question for the whole project: maybe the challenge isn't finding the signal. Maybe it's finding *when* the signal works.

---

## How to run it

This picks up directly from `feature_set.py` in the Day 5 folder — `features_df` needs to already exist in your session before running this.

```bash
pip install matplotlib seaborn

python day6_analysis.py
```

---

## Files

```
day06-data-analysis/
├── day6_analysis.py    # stats questions + 3 visualizations + equity curve
└── README.md
```

---

## What comes next

Figuring out when relative strength actually works versus when it doesn't — because right now the equity curve says it's not consistent enough on its own.

#QuantFinance #AlgoTrading #Python #BuildingInPublic
