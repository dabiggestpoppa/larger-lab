"""
FIBONACCI SEQUENCE SCANNER
Reconstructs sequence rules from Holy Grail Excel + extracted data.
"""
import json, csv
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QL = REPO_ROOT / "quant-lab"
EXT = QL / "reports" / "predecessor" / "extracted"

# ── Load extracted data ─────────────────────────────────────────────────

def load_sheet(n):
    return json.load(open(EXT / "sheet_data" / f"sheet_{n:03d}.json"))

def load_csv(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))

print("Loading Holy Grail data...")

# Sheet 006 = Fibonacci Sequences Catalog
fib_catalog = load_sheet(6)
print(f"  Catalog: {fib_catalog['row_count']} rows")

# Asian Fibonacci CSV
asian_fib = load_csv(EXT / "price_data" / "EURUSD_Asian_Fibonacci.csv") if (EXT / "price_data" / "EURUSD_Asian_Fibonacci.csv").exists() else []
print(f"  Asian Fib: {len(asian_fib)} sessions")

# Monday Fibonacci CSV
monday_fib = load_csv(EXT / "price_data" / "EURUSD_Monday_Fibonacci.csv") if (EXT / "price_data" / "EURUSD_Monday_Fibonacci.csv").exists() else []
print(f"  Monday Fib: {len(monday_fib)} weeks")

# ── Extract sequence catalog ────────────────────────────────────────────

print("\n" + "=" * 70)
print("FIBONACCI SEQUENCE CATALOG")
print("=" * 70)

SEQUENCES = []
for row in fib_catalog["data"]:
    name = row.get("Sequence Name", "")
    if name and name != "Sequence Name":
        seq = {k: v for k, v in row.items() if k != "col_8"}
        SEQUENCES.append(seq)
        print(f"  {name}: {row.get('Completion Rate','')} completion | {row.get('Frequency (%)','')}% freq | {row.get('Timeframe','')}")

# ── Analyze Asian Fib (intraday) ────────────────────────────────────────

print("\n" + "=" * 70)
print("EURUSD ASIAN FIBONACCI — INTRADAY HIT RATES")
print("=" * 70)

if asian_fib:
    N = len(asian_fib)
    bull = sum(1 for r in asian_fib if r.get("bias") == "Bullish")
    bear = sum(1 for r in asian_fib if r.get("bias") == "Bearish")
    print(f"\n  Sessions: {N} (Bullish={bull} {bull/N*100:.1f}% / Bearish={bear} {bear/N*100:.1f}%)")

    # Count exact and tolerance hits
    levels = ["hit_25", "hit_50", "hit_100", "hit_168", "hit_132_violation"]
    tol_levels = ["hit_25_tol", "hit_50_tol", "hit_100_tol", "hit_168_tol", "hit_132_violation_tol"]
    labels = {"hit_25": "-25%", "hit_50": "-50%", "hit_100": "-100%", "hit_168": "-168%", "hit_132_violation": "132% viol"}

    print(f"\n  {'Level':<14} {'Exact':>10} {'±Tol':>10} {'Diff':>8}")
    print(f"  {'-'*44}")
    for lvl in levels:
        exact = sum(1 for r in asian_fib if r.get(lvl, "").strip().lower() == "true")
        tol_key = lvl + "_tol"
        tol = sum(1 for r in asian_fib if r.get(tol_key, "").strip().lower() == "true")
        er = exact / N * 100
        tr = tol / N * 100
        print(f"  {labels[lvl]:<14} {er:>8.1f}% {tr:>8.1f}% {tr-er:>+7.1f}%")

    # Sequence patterns
    print(f"\n  Top hit sequences (exact):")
    seq_counts = defaultdict(int)
    for r in asian_fib:
        parts = []
        for lvl in ["hit_25", "hit_50", "hit_100", "hit_168"]:
            if r.get(lvl, "").strip().lower() == "true":
                parts.append(lvl.replace("hit_", ""))
        if parts:
            seq_counts["→".join(parts)] += 1
    for seq, cnt in sorted(seq_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    {seq}: {cnt} ({cnt/N*100:.1f}%)")

# ── Analyze Monday Fib (weekly) ─────────────────────────────────────────

print("\n" + "=" * 70)
print("EURUSD MONDAY FIBONACCI — WEEKLY HIT RATES")
print("=" * 70)

if monday_fib:
    N = len(monday_fib)
    bull = sum(1 for r in monday_fib if r.get("Directional_Bias") == "Bullish")
    bear = sum(1 for r in monday_fib if r.get("Directional_Bias") == "Bearish")
    print(f"\n  Weeks: {N} (Bullish={bull} {bull/N*100:.1f}% / Bearish={bear} {bear/N*100:.1f}%)")

    weekly_keys = ["Fib_25_Hit", "Fib_50_Hit", "Fib_100_Hit", "Fib_168_Hit", "Fib_132_Violated"]
    weekly_labels = {"Fib_25_Hit": "-25%", "Fib_50_Hit": "-50%", "Fib_100_Hit": "-100%", "Fib_168_Hit": "-168%", "Fib_132_Violated": "132% viol"}

    print(f"\n  {'Level':<14} {'Hits':>8} {'Rate':>8}")
    print(f"  {'-'*32}")
    for key in weekly_keys:
        hits = sum(1 for r in monday_fib if r.get(key, "").strip().lower() == "true")
        print(f"  {weekly_labels[key]:<14} {hits:>7} {hits/N*100:>7.1f}%")

# ── Intraday vs Weekly comparison ───────────────────────────────────────

print("\n" + "=" * 70)
print("COMPARISON: INTRADAY vs WEEKLY (EURUSD)")
print("=" * 70)

if asian_fib and monday_fib:
    N_i = len(asian_fib)
    N_w = len(monday_fib)

    intraday_rates = {}
    for lvl, key in [("-25%", "hit_25"), ("-50%", "hit_50"), ("-100%", "hit_100"), ("-168%", "hit_168"), ("132%", "hit_132_violation")]:
        hits = sum(1 for r in asian_fib if r.get(key, "").strip().lower() == "true")
        intraday_rates[lvl] = hits / N_i * 100

    weekly_rates = {}
    for lvl, key in [("-25%", "Fib_25_Hit"), ("-50%", "Fib_50_Hit"), ("-100%", "Fib_100_Hit"), ("-168%", "Fib_168_Hit"), ("132%", "Fib_132_Violated")]:
        hits = sum(1 for r in monday_fib if r.get(key, "").strip().lower() == "true")
        weekly_rates[lvl] = hits / N_w * 100

    print(f"\n  {'Level':<12} {'Intraday':>10} {'Weekly':>10} {'Diff':>10}")
    print(f"  {'-'*44}")
    for lvl in ["-25%", "-50%", "-100%", "-168%", "132%"]:
        ir = intraday_rates.get(lvl, 0)
        wr = weekly_rates.get(lvl, 0)
        print(f"  {lvl:<12} {ir:>9.1f}% {wr:>9.1f}% {wr-ir:>+9.1f}%")

# ── Save sequence rules ─────────────────────────────────────────────────

RULES = {
    "levels": {"-25%": 0.25, "-50%": 0.50, "-100%": 1.00, "-168%": 1.68, "132%_rekey": 1.32},
    "sequences": [
        {"name": "Full Extension", "pattern": ["-25%→-50%→-100%→-168%"], "freq": "28/103", "completion": "87.2%", "duration": "8-12h"},
        {"name": "Rekey Trigger", "pattern": ["-25%→-50%→132%"], "freq": "18/103", "completion": "100%", "duration": "6-8h"},
        {"name": "Partial Delivery", "pattern": ["-25%→-50%"], "freq": "24/103", "completion": "96.4%", "duration": "4-6h"},
        {"name": "Direct Invalidation", "pattern": ["-25%→132%"], "freq": "12/103", "completion": "100%", "duration": "3-5h"},
        {"name": "Double Rekey 132→168", "pattern": ["132%→168%"], "freq": "90/103 (87.4%)", "duration": "1.8h", "note": "Dominant pattern"},
        {"name": "Double Rekey 168→132", "pattern": ["168%→132%"], "freq": "13/103 (12.6%)", "duration": "3.9h", "note": "Slower reversal"},
        {"name": "50%→50% Retest", "pattern": ["50%→50%"], "freq": "83-91%", "completion": "Highest success", "note": "Alpha sequence initiation"},
    ],
    "pullbacks": {"-25%": 29, "-50%": 27.8, "132%": 26.8, "168%": 24.2},
    "bias_rule": "Bullish if Session_Close > Session_Open, Bearish if Close < Open",
    "tolerance": "2 pips",
}

out = QL / "scripts" / "fib_sequence_rules.json"
with open(out, "w") as f:
    json.dump(RULES, f, indent=2)

print(f"\nSequence rules saved: {out}")
print("\nDONE.")
