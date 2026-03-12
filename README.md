# CAID State Spotlight Guide

Resources for writing state-level AI legislation reports using the [CAID State AI Legislation Tracker](https://du-caid.github.io/tracker/).

## In the repo

| File | What it is |
|---|---|
| `docs/state-spotlight-analyst-guide.md` | guide for researching and writing a state spotlight report |
| `scripts/analyze_state.py` | Python script that pulls bill data for any state and prints a structured summary |

---

## Quick start

```bash
# Install dependencies (just requests and beautifulsoup4 - standard library otherwise)
pip install requests

# Run for any state (fetches live from the public dashboard)
python scripts/analyze_state.py CO
python scripts/analyze_state.py NY
python scripts/analyze_state.py CA

# Save output to a file
python scripts/analyze_state.py CO > co_summary.txt
```

Then read `docs/state-spotlight-analyst-guide.md` for how to interpret the output and structure your report.

---

## Data source

All data comes from the public CAID dashboard:

- **Dashboard**: https://du-caid.github.io/tracker/
- **State bill data**: `https://du-caid.github.io/tracker/data/bills_by_state/<ST>.json`

No database access or internal files needed. The script grabs everything from the dashboard.

---
