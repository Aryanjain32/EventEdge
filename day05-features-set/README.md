# Day 5 — The Same Earnings Report, Two Different Reactions

Code from Day 5 of building EventEdge, an event-driven quant model for NSE stocks, in public.

Same earnings beat. Same company. Two completely different market reactions, depending entirely on what the broader market was doing that day.

A positive surprise during a bull run → aggressive buying, stock jumps.
The exact same surprise during a panic phase → muted response, stock barely moves.

The event is identical. The market around it isn't.

That single observation is why this isn't just about the stock anymore. It's about the environment the stock sits in. So NIFTY enters the picture today.

---

## What this script does

Builds the first real feature set on top of the earnings events from `quarterly_reports.csv`. Five features, each one a hypothesis about what actually drives the reaction.

**1. PreEventReturn** — what was the stock doing in the 5 days before the event?
A stock up 20% pre-earnings is priced very differently from one that's been falling for months. Same beat, different setup.

**2. VolumeRatio** — today's volume vs the 20-day average.
Price tells you what happened. Volume tells you the conviction behind it. 3% up on low volume isn't the same signal as 3% up on double the normal volume.

**3. Nifty1D_Return / Nifty5D_Return** — what was NIFTY doing on the event day, and into it?
This is the market's emotional state. When NIFTY is falling sharply, even genuinely good news struggles to move a stock.

**4. RelativeStrength5D** — PreEventReturn minus Nifty5D_Return.
Is the stock actually outperforming the market, or just riding a broad rally? Two stocks can both be "up 5% before earnings" and mean opposite things depending on what NIFTY did that same week.

**5. RelativeStrength1D** — Return1D minus Nifty1D_Return.
Same idea, applied to the reaction itself. A stock +2% while NIFTY is -2% is a much stronger signal than +2% while NIFTY is +3%.

---

## Why each feature is really a hypothesis

This is the part I keep coming back to. Every feature added here is a bet on what matters:

- Adding momentum → betting that recent behavior influences future behavior
- Adding volume → betting that participation level carries information
- Adding NIFTY → betting that market sentiment shapes individual reactions
- Adding relative strength → betting that outperformance itself is signal

None of these are proven yet. That's what the model is for. Right now I'm just making sure the right hypotheses are even on the table before any algorithm gets near them.

---

## How to run it

```bash
pip install yfinance pandas

python feature_set.py
```

`quarterly_reports.csv` needs to be in the same folder.

---

## Files

```
day05-feature-set/
├── feature_set.py          # events + base features + NIFTY benchmark + relative strength
├── quarterly_reports.csv
└── README.md
```

---

## What comes next

Running stats on these five features to see which ones actually hold up before any ML model touches them.

#QuantFinance #AlgoTrading #Python #BuildingInPublic
