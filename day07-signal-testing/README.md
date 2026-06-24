# Day 7 — Testing the Signal

Code from Day 7 of building EventEdge, an event-driven quant model for NSE stocks, in public.

Finding a pattern is easy. Proving it isn't.

Relative Strength looked like the strongest signal coming out of Day 6. But a convincing chart isn't evidence. I needed a real test: is this actually predictive, or am I just seeing what I want to see?

---

## What this script does

Takes every feature I'd built so far and tests it the same rigorous way. Splits all observations into 5 equal buckets by feature value — weakest 20% to strongest 20% — and measures the average 3-day return inside each bucket. If a feature is real signal, returns should separate cleanly across the buckets. If it's noise, the buckets come back scrambled.

Ran this on 6 features.

---

## What came back

**🏆 RelativeStrength1D — strongest signal by far (+2.69% spread)**
Bottom 20%: -0.98% → Top 20%: +1.70%. Almost a straight line across all 5 buckets. Stocks that beat the market on earnings day itself kept outperforming for the next 3 sessions. This looks like genuine Post-Earnings Announcement Drift in NSE stocks — now my primary signal.

**🚀 GapPct — bigger gaps really do perform better (+1.21% spread)**
Top 20% of gaps: +1.02% over 3 days. Flat or negative gaps lose money. Big gaps don't seem to get faded here — they look more like a structural shock, with institutions caught off guard and forced to keep buying for days.

**⏱️ RelativeStrength5D — matters, but not how I expected (+1.38% spread)**
Bottom 3 buckets all negative, around -0.4%. Then a jump: 60-80% bucket hits +1.15%, but the Top 20% bucket actually drops to +0.86%. My read: the most hyped pre-earnings stocks are already a little priced in by the time the event hits. The 60-80% range looks more like quiet accumulation without the retail hype layered on top.

**📈 PreEventReturn — winners keep winning (+1.16% spread)**
Top 20%: +0.88% → Bottom 20%: -0.27%. Clean and monotonic. Stocks already trending up before earnings tend to keep drifting higher afterward.

**🌍 Nifty1D_Return — regime matters, but not linearly (+0.82% spread)**
Bad market day: -0.63%. Flat-to-mildly-up day: +0.91%. Massive rally day: flattens to +0.17%. Panic drags everything down together. Euphoria pulls capital into the broad index instead of individual earnings plays.

**❌ VolumeRatio — pure noise (-0.03% spread)**
Top bucket: +0.48% → Bottom bucket: +0.50%. Practically identical, with no pattern in between. Every stock spikes in volume on earnings day, good news or bad — so on its own, volume tells you nothing about direction.

---

## Where this leaves things

Relative Strength — both the 1-day post-event version and the 5-day pre-event version — is doing the real work here. The event itself (the gap) matters too, but less than how the stock and the market were already positioned going in.

VolumeRatio is likely getting dropped from the model entirely, or kept only as a confirmation filter rather than a standalone signal.

---

## How to run it

This continues directly from `features_df`, built in the Day 5 folder. Run that first, then this.

```bash
pip install pandas

python quantile_analysis.py
```

---

## Files

```
day07-signal-testing/
├── quantile_analysis.py   # 5-bucket quantile test across all 6 features
└── README.md
```

---

## What comes next

Building a composite strategy that combines the strongest factors together, and checking whether stacking them actually improves on any single one.

#QuantFinance #AlgoTrading #Python #BuildingInPublic
