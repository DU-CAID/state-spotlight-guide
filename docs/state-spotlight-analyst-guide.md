# State Spotlight Report Guide

## Overview

The CAID State AI Legislation Tracker publishes all its data as public JSON files hosted on GitHub Pages. You don't need access to the DuckDB database or any internal files to do a state spotlight analysis. Everything you need for the quantitative layer is available at:

```
https://du-caid.github.io/tracker/data/bills_by_state/<STATE>.json
```

Replace `<STATE>` with the two-letter state abbreviation (e.g., `CO`, `NY`, `CA`).

For the qualitative layer - bill text, sponsor details, committee votes, amendment history - you'll use the state legislature's own website, linked directly from the data.

---

## Step 1: Run the starter ccript

The script `scripts/analyze_state.py` does all the quantitative work automatically. Run it like this:

```bash
python scripts/analyze_state.py CO
```

It will print a structured summary: bill counts by year and tier, top AI concepts, a full list of core AI bills with their status, and NCSL-confirmed laws. This output is the data foundation. Write it down, paste it into a working document, and use it to structure your report.

You can run it for any state:
```bash
python scripts/analyze_state.py NY
python scripts/analyze_state.py CA
python scripts/analyze_state.py TX
```

---

## Step 2: Understand the data schema

Each bill record in the JSON has these fields:

| Field | What it means | Always populated? |
|---|---|---|
| `identifier` | Bill number, e.g. `HB 24-1147` or `SB 25B-004` | Yes |
| `title` | Short official title | For ~67% of bills |
| `session` | Legislative session, e.g. `2024A`, `2025B` | Yes |
| `state` | Two-letter state code | Yes |
| `core_ai_hits` | Number of core AI keyword matches in the bill text | Yes |
| `adjacent_ai_hits` | Number of adjacent AI keyword matches | Yes |
| `matched_concepts` | List of AI concept categories matched (see below) | Yes |
| `matched_tiers` | `core_ai`, `adjacent_ai`, and/or `ncsl` | Yes |
| `in_ncsl` | Whether NCSL independently tracks this as an AI law | Yes |
| `ncsl_status` | NCSL's status label (e.g., `Enacted`, `Vetoed`) | ~22% |
| `source_bucket` | `regex_flagged` (our pipeline found it) or `ncsl_only` (NCSL found it, we didn't) | Yes |
| `latest_action_date` | Date of most recent legislative action | ~67% |
| `latest_action_description` | Text description of most recent action | ~67% |
| `primary_url` | Direct link to bill text on the state legislature site | Yes |

### What's NOT in the public JSON

- **Sponsor names** - you'll need to look these up on the state legislature website
- **Vote counts** - same
- **Full bill text** - available via `primary_url`
- **Amendment history** - available on the state legislature website

---

## Step 3: Understand the key concepts

The `matched_concepts` field tells you which type of AI the bill addresses. Here's what each value means:

| Concept | Plain English |
|---|---|
| `artificial_intelligence` | Bill explicitly mentions "artificial intelligence" |
| `machine_learning` | Bill mentions "machine learning" |
| `ai_system_composite` | Bill uses regulatory compound phrases like "AI system" or "automated decision system" |
| `algorithmic_tool` | Bill addresses algorithmic tools or systems (often pricing, hiring, lending) |
| `algorithmic_decision_system` | Narrower term for automated decision-making systems |
| `automated_decision_system` | Similar - automated systems making decisions affecting people |
| `high_risk_ai_variant` | Bill uses "high-risk AI" or similar regulatory framing |
| `deepfake_media` | Bill addresses synthetic/AI-generated media (deepfakes) |
| `generative_ai` / `generative_ai_variant` | Bill mentions generative AI or large language models |
| `llm_variant` | Bill mentions "large language model" or "LLM" |
| `foundation_model` | Bill mentions foundation models |
| `ai_model_variant` | Broad AI model language |
| `adjacent_tech` | Technology adjacent to AI (e.g., autonomous vehicles, sensors) - not core AI |
| `ncsl_curated_ai_law` | NCSL identified this as an AI law; our workflow may not have matched it |

**Important:** A bill is **Core AI** if `core_ai_hits > 0`. It's **Adjacent AI** if `adjacent_ai_hits > 0` but `core_ai_hits == 0`. These are not mutually exclusive at the concept level, but the tier classification is.

---

## Step 4: Classify bill outcomes

The `latest_action_description` field uses raw legislative action text. Here's how to interpret the most common patterns:

| Action text contains... | What it means |
|---|---|
| `Governor Signed` | **Enacted** - became law |
| `Governor Vetoed` | **Vetoed** - passed legislature, rejected by governor |
| `Postpone Indefinitely` | **Failed** - killed in committee |
| `Lay Over Unamended - Amendment(s) Failed` | **Failed** - stuck in appropriations or amendments failed |
| `Laid Over Daily` | **In progress** - active, not yet resolved |
| `Introduced In House` / `Introduced In Senate` | **Early stage** - just introduced |
| `Third Reading` / `Second Reading` | **Active floor consideration** |
| `Sent to the Governor` / `Enrolled` | **Awaiting signature** |

Bills with no `latest_action_description` are usually NCSL-only records - NCSL tracks them, but we don't have full action data in our workflow.

---

## Step 5: Read bills qualitatively

For each core AI bill you want to discuss in depth:

1. Find it in the script output or JSON
2. Click (or copy) the `primary_url` - this goes directly to the bill text
3. On the state legislature site, you can also find:
   - **Sponsors**: listed on the bill's main page
   - **Committee assignments**: in the bill history
   - **Vote counts**: under the bill actions tab
   - **Amended versions**: multiple PDFs if the bill was amended

For Colorado specifically, the URL pattern for the legislature landing page is:
```
https://leg.colorado.gov/bills/hb24-1147   (House Bill)
https://leg.colorado.gov/bills/sb24-205    (Senate Bill)
https://leg.colorado.gov/bills/sb25b-004   (Special session)
```

---

## Step 6: Structure the report

A state spotlight report typically covers:

1. **Headline numbers** - total bills, core AI bills, laws enacted, trends over time
2. **Legislative waves or phases** - how has the volume and character of legislation changed year by year?
3. **Dominant policy themes** - what subjects keep coming up? (consumer protection, deepfakes, algorithmic pricing, government AI, etc.)
4. **What passed vs. what failed** - and what explains the difference?
5. **Key legislators** - who sponsors most of the AI bills? Any recurring patterns?
6. **Implications** - what does this tell practitioners/policymakers in this state or watching this state?
7. **What to watch** - bills currently in progress or themes likely to resurface

The Colorado spotlight report (`reports/colorado-ai-legislation-2026-q1.html`) is a good template to follow for structure, length, and tone.

---

## Limitations to keep in mind

- **Not all bills have titles** - about 1/3 of records are NCSL-only and lack titles, action descriptions, and sponsor data. Focus your qualitative analysis on the `regex_flagged` bills that have full data.
- **Session labels vary by state** - some states use calendar years (2024, 2025), others use session numbers or codes. The script handles year extraction, but be aware when you see unusual session labels.
- **"Passed" ≠ "enacted"** - a bill can pass one chamber and fail in the other. The `latest_action_description` reflects the most recent status, not the final outcome for bills still in progress.
- **Sponsor data is not in the public JSON** - you have to look up sponsors on the state legislature website. For multi-sponsor bills, the first listed sponsor is typically the primary.
- **Data is updated periodically** - the tracker is refreshed regularly but not in real time. Very recent actions may not yet be reflected.

---

## Quick Reference: Useful Dashboard Links

- **Dashboard (all states)**: https://du-caid.github.io/tracker/
- **Bill browser for a specific state**: use the Bill Browser tab, filter by state
- **State JSON files**: `https://du-caid.github.io/tracker/data/bills_by_state/<ST>.json`
- **Summary data**: `https://du-caid.github.io/tracker/data/summary.json`
- **Concepts data**: `https://du-caid.github.io/tracker/data/concepts.json`
- **Bills by year**: `https://du-caid.github.io/tracker/data/by_year.json`
