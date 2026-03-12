"""
analyze_state.py - CAID State AI Legislation Report Template Script
====================================================================
Pulls bill data for any U.S. state from the public CAID dashboard
and prints a structured summary for use in state spotlight reports.

Usage:
    python scripts/analyze_state.py CO          # fetch live from dashboard
    python scripts/analyze_state.py CO --local  # use local copy in tracker/data/

Output is printed to the terminal. Redirect to a file if you want to save it:
    python scripts/analyze_state.py CO > co_summary.txt

See docs/state-spotlight-report-guide.md for how to interpret the output.

Last update: 11 March 2026 (Stefani Langehennig)
"""

import sys
import json
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

# config

DASHBOARD_URL = "https://du-caid.github.io/tracker/data/bills_by_state/{state}.json"

# path to local dashboard data (if running with --local)
LOCAL_DATA_DIR = Path(__file__).parent.parent / "dashboard" / "data" / "bills_by_state"

# human-readable labels for matched_concepts
CONCEPT_LABELS = {
    "artificial_intelligence":    "Artificial Intelligence",
    "machine_learning":           "Machine Learning",
    "ai_system_composite":        "AI System (regulatory framing)",
    "algorithmic_tool":           "Algorithmic Tools",
    "algorithmic_decision_system":"Algorithmic Decision Systems",
    "automated_decision_system":  "Automated Decision Systems",
    "high_risk_ai_variant":       "High-Risk AI",
    "deepfake_media":             "Deepfakes / Synthetic Media",
    "generative_ai":              "Generative AI",
    "generative_ai_variant":      "Generative AI (variant)",
    "llm_variant":                "Large Language Models",
    "foundation_model":           "Foundation Models",
    "ai_model_variant":           "AI Model (general)",
    "adjacent_tech":              "Adjacent Technology",
    "ncsl_curated_ai_law":        "NCSL-Curated AI Law",
}


# outcome classification

def classify_outcome(bill):
    """Return a short outcome label based on latest_action_description."""
    desc = (bill.get("latest_action_description") or "").lower()
    ncsl = (bill.get("ncsl_status") or "").lower()

    if "governor signed" in desc or ncsl in ("enacted", "signed"):
        return "Signed"
    if "governor vetoed" in desc or ncsl == "vetoed":
        return "Vetoed"
    if "postpone indefinitely" in desc:
        return "Failed (committee)"
    if "lay over unamended" in desc or "amendment(s) failed" in desc:
        return "Failed (appropriations)"
    if "lost" in desc:
        return "Failed (floor)"
    if "introduced" in desc:
        return "Introduced"
    if "sent to the governor" in desc or "enrolled" in desc:
        return "Awaiting signature"
    if desc:
        return "In progress"
    return "Unknown"


def is_signed(bill):
    return classify_outcome(bill) == "Signed"


def is_failed(bill):
    return classify_outcome(bill).startswith("Failed")


# year extraction

def extract_year(session):
    """Extract a 4-digit calendar year from a session string, or return None."""
    import re
    m = re.search(r'(19|20)\d{2}', str(session))
    if m:
        yr = int(m.group())
        if 1990 <= yr <= 2035:
            return str(yr)
    return None


# loading data

def load_bills(state, local=False):
    state = state.upper()
    if local:
        path = LOCAL_DATA_DIR / f"{state}.json"
        if not path.exists():
            sys.exit(f"Local file not found: {path}\nTry without --local to fetch from the web.")
        print(f"[loading from local file: {path}]", file=sys.stderr)
        return json.loads(path.read_text(encoding="utf-8"))
    else:
        url = DASHBOARD_URL.format(state=state)
        print(f"[fetching {url}]", file=sys.stderr)
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            sys.exit(f"Could not fetch data: {e}\nTry --local if you have a local copy.")


# functions for analysis 

def section(title):
    width = 70
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def subsection(title):
    print()
    print(f"--- {title} ---")


def analyze(bills, state):
    core   = [b for b in bills if b.get("core_ai_hits", 0) > 0]
    adj    = [b for b in bills if b.get("core_ai_hits", 0) == 0
                               and b.get("adjacent_ai_hits", 0) > 0]
    flagged = core + adj   # pipeline-found bills (have titles and action data)
    ncsl_only = [b for b in bills if b.get("source_bucket") == "ncsl_only"]

    # headline numbers
    section(f"STATE AI LEGISLATION SUMMARY: {state.upper()}")
    print(f"\n  Total bills in tracker:    {len(bills):>4}")
    print(f"  Core AI bills:             {len(core):>4}  (AI is primary subject)")
    print(f"  Adjacent AI bills:         {len(adj):>4}  (AI appears as a tool)")
    print(f"  NCSL-only records:         {len(ncsl_only):>4}  (tracked by NCSL, limited data)")
    print()

    # core AI outcomes
    signed  = [b for b in core if is_signed(b)]
    failed  = [b for b in core if is_failed(b)]
    vetoed  = [b for b in core if classify_outcome(b) == "Vetoed"]
    other   = [b for b in core if not is_signed(b) and not is_failed(b)
                                  and classify_outcome(b) != "Vetoed"]
    print(f"  Core AI bill outcomes:")
    print(f"    Signed into law:         {len(signed):>4}")
    print(f"    Vetoed:                  {len(vetoed):>4}")
    print(f"    Failed (committee/floor):{len(failed):>4}")
    print(f"    In progress / unknown:   {len(other):>4}")

    # bills by year 
    subsection("CORE AI BILLS BY YEAR")
    year_core = Counter()
    year_adj  = Counter()
    for b in core:
        yr = extract_year(b.get("session", ""))
        if yr:
            year_core[yr] += 1
    for b in adj:
        yr = extract_year(b.get("session", ""))
        if yr:
            year_adj[yr] += 1

    all_years = sorted(set(year_core) | set(year_adj))
    print(f"\n  {'Year':<8} {'Core AI':>9} {'Adjacent':>10} {'Total':>7}")
    print(f"  {'-'*8} {'-'*9} {'-'*10} {'-'*7}")
    for yr in all_years:
        c = year_core.get(yr, 0)
        a = year_adj.get(yr, 0)
        print(f"  {yr:<8} {c:>9} {a:>10} {c+a:>7}")

    # top concepts
    subsection("TOP MATCHED CONCEPTS (core AI bills only)")
    concept_counts = Counter()
    for b in core:
        for c in b.get("matched_concepts", []):
            if c != "ncsl_curated_ai_law":
                concept_counts[c] += 1

    print()
    for concept, n in concept_counts.most_common(15):
        label = CONCEPT_LABELS.get(concept, concept)
        bar = "#" * n
        print(f"  {label:<40} {n:>3}  {bar}")

    # core AI bill list
    subsection("ALL CORE AI BILLS (sorted by session)")
    print()
    print(f"  {'Session':<10} {'Identifier':<14} {'Outcome':<28} {'Title'}")
    print(f"  {'-'*10} {'-'*14} {'-'*28} {'-'*40}")

    for b in sorted(core, key=lambda x: (x.get("session", ""), x.get("identifier", ""))):
        outcome = classify_outcome(b)
        session = b.get("session", "")
        ident   = b.get("identifier", "")
        title   = b.get("title", "(no title)") or "(no title)"
        if len(title) > 55:
            title = title[:52] + "..."
        print(f"  {session:<10} {ident:<14} {outcome:<28} {title}")

    # NCSL-confirmed 
    ncsl_confirmed = [b for b in bills if b.get("in_ncsl")]
    if ncsl_confirmed:
        subsection("NCSL-CONFIRMED AI LAWS")
        print(f"\n  {len(ncsl_confirmed)} bills confirmed by NCSL as AI-related laws.\n")
        for b in sorted(ncsl_confirmed, key=lambda x: (x.get("session",""), x.get("identifier",""))):
            status = b.get("ncsl_status") or classify_outcome(b)
            title  = b.get("title", "") or "(no title)"
            print(f"  {b.get('session',''):<10} {b.get('identifier',''):<14} [{status}]  {title[:50]}")

    # signed laws details
    subsection("SIGNED CORE AI LAWS — DETAIL")
    print()
    for b in sorted(signed, key=lambda x: (x.get("session",""), x.get("identifier",""))):
        title    = b.get("title", "(no title)") or "(no title)"
        concepts = ", ".join(
            CONCEPT_LABELS.get(c, c)
            for c in b.get("matched_concepts", [])
            if c not in ("ncsl_curated_ai_law", "adjacent_tech")
        )
        url = b.get("primary_url", "")
        print(f"  {b.get('session',''):<10} {b.get('identifier',''):<14} {title}")
        if concepts:
            print(f"             Concepts: {concepts}")
        if url:
            print(f"             URL:      {url}")
        print()

    # failed bills details
    subsection("FAILED / VETOED CORE AI BILLS — DETAIL")
    print()
    for b in sorted(failed + vetoed, key=lambda x: (x.get("session",""), x.get("identifier",""))):
        title   = b.get("title", "(no title)") or "(no title)"
        outcome = classify_outcome(b)
        action  = b.get("latest_action_description", "") or ""
        url     = b.get("primary_url", "")
        print(f"  {b.get('session',''):<10} {b.get('identifier',''):<14} [{outcome}]  {title}")
        if action:
            print(f"             Last action: {action[:80]}")
        if url:
            print(f"             URL:         {url}")
        print()

    # report writing quick ref
    section("QUICK REFERENCE FOR REPORT WRITING")
    print(f"""
  Use these numbers in your report introduction:

    "{state.upper()} has introduced {len(bills)} AI-related bills in the CAID tracker,
    including {len(core)} core AI bills where AI is the primary legislative subject.
    Of those, {len(signed)} have been signed into law."

  Top themes to research further (based on concept frequency):
""")
    for concept, n in concept_counts.most_common(5):
        label = CONCEPT_LABELS.get(concept, concept)
        print(f"    - {label} ({n} bills)")

    print(f"""
  Next steps:
    1. Review the bill list above and open each URL to read the actual legislation
    2. Look up sponsors on the state legislature website — not in this data
    3. Search leg.colorado.gov (or your state's equivalent) for committee votes
    4. See docs/state-spotlight-analyst-guide.md for full interpretation notes
""")


# entry point

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    state = args[0].upper()
    local = "--local" in args

    bills = load_bills(state, local=local)
    analyze(bills, state)
