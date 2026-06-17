# Day 3 — 4 Versions, Same Goal, None Worked the Way I Expected

Code from Day 3 of building EventEdge, an event-driven quant model for NSE stocks, in public.

4 versions of the same script. Same goal each time: collect NSE earnings announcements.

The assumption I walked in with: if an API endpoint exists, make a request, get JSON, move on.
That lasted about 4 minutes.

---

## What broke, version by version

**v2 — smart_matching.py**
Got the API returning data using a Chrome-impersonated session (curl_cffi + cookies, fixed on Day 2). Thought I'd solved it. Then noticed the earnings filter was returning far fewer results than expected.

**v3 — broader_filter.py**
Looked at the raw records more carefully. NSE doesn't standardize announcement subjects. Some say "Quarterly Results." Some say "Financial Results." Some bury the relevant info in the description field, not the subject line. Expanded the filter to catch every variation, and added a fail-safe that checks every known key NSE uses for timestamps, since that's inconsistent too.

**v4 — json_structure_fix.py**
Hit a new problem: inconsistent JSON structure. Some responses come back as a plain list, some wrap the data inside a `"rows"` key, some inside a `"data"` key. Fields I expected occasionally didn't exist. New fields showed up unexpectedly. Spent more time investigating the data than writing model logic.

**Final — data_pipeline_final.py**
Stepped back entirely. Instead of querying company by company, switched to downloading a master NSE dataset once and filtering it locally with pandas. That shift — from "fetch what I need" to "build infrastructure I can trust" — changed how I think about the rest of this project.

It didn't fully work either. Here's the actual output from running it:

```
Connecting to NSE to download master corporate filings directory...
  ↳ Successfully parsed 20 total corporate records across all NSE listings.
Processing calculations for RELIANCE...
  ↳ No historical quarterly filings noted for RELIANCE within the active slice.
Completed mapping data metrics for RELIANCE.

Processing calculations for TCS...
  ↳ No historical quarterly filings noted for TCS within the active slice.
Completed mapping data metrics for TCS.

Processing calculations for HDFCBANK...
  ↳ No historical quarterly filings noted for HDFCBANK within the active slice.
Completed mapping data metrics for HDFCBANK.

=== Data Mismatch Notice ===
Prices generated cleanly but flags remained unassigned. Sample price rows:
Price             Open       Close  EarningsFlag
Date
2020-01-01  679.081936  675.324158         False
2020-01-02  676.397899  686.821228         False
2020-01-03  685.792252  687.648804         False
```

20 records across the entire NSE listing universe, going back 5 years. That's not a real dataset, that's a sign the master CSV export itself isn't returning what I think it's returning. The architecture is right, but there's still a gap between "the code runs without errors" and "the code is doing what I designed it to do."

That gap is the actual lesson of Day 3.

---

## The part that actually mattered: event alignment

This surprised me more than any of the API issues.

A company releases earnings at 2 PM during market hours → the market reacts immediately.
Same report released after market close → the reaction doesn't show up until the next trading session.

If I label the event date wrong, the model thinks the stock reacted before the announcement even existed.

That's not a code bug. That's a flaw in the research design itself. One small timing error makes the entire analysis meaningless.

Most people think quant research fails at the model stage. It usually fails at the data stage, before the model even exists. Day 3 made that real for me twice over — first with the API itself, then with the master CSV silently returning far less data than it should.

---

## How to run it

```bash
pip install yfinance curl_cffi pandas

python data_pipeline_final.py
```

---

## Files

```
day03-data-pipeline-v2/
├── data_pipeline_final.py     # final version — bulk CSV approach (still debugging the data gap)
├── drafts/
│   ├── v2_smart_matching.py
│   ├── v3_broader_filter.py
│   └── v4_json_structure_fix.py
└── README.md
```

---

## What comes next

Day 4 picks up from here, tracking down why the master CSV is only returning 20 records, and getting earnings flags actually populated before moving on to feature engineering.

#QuantFinance #AlgoTrading #Python #BuildingInPublic
