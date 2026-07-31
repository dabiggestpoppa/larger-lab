"""
Full Basket Breakdown — All Assets, All Operating Points
=========================================================
Per-pair: Gross PnL -> Spread cost -> Commission -> Net PnL
Grouped by FLOOR, KNEE, CEILING baskets.
"""

import json
import os

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

# Current spreads from MT5 (pips)
SPREADS = {
    "EURUSD": 0.20, "USDJPY": 0.20, "CHFJPY": 1.40,
    "NZDUSD": 0.20, "AUDUSD": 0.30, "USDCHF": 0.70, "GBPJPY": 1.00,
}
DEFAULT_SPREAD = 0.50
COMM_PER_TRADE = 0.07


def get_pip_value(pair):
    return 0.07 if "JPY" in pair else 0.10


def clean_symbol(sym):
    return sym.replace(".PRO", "").replace("_PRO", "")


def calc_costs(trades, gross_pnl_pips, spread_pips, pip_val):
    gross_usd = gross_pnl_pips * pip_val
    sprd_usd = trades * spread_pips * pip_val
    comm_usd = trades * COMM_PER_TRADE
    net_usd = gross_usd - sprd_usd - comm_usd
    cost_pct = (sprd_usd + comm_usd) / gross_usd * 100 if gross_usd > 0 else 0
    return gross_usd, sprd_usd, comm_usd, net_usd, cost_pct


# ── Load all sweep data ──
all_entries = {}  # {clean_sym: [entry, ...]}

sweep_files = [f for f in os.listdir(REPORTS_DIR)
               if "sweep" in f.lower() and f.endswith(".json") and "crypto" not in f.lower()]

for fname in sweep_files:
    fpath = os.path.join(REPORTS_DIR, fname)
    with open(fpath) as f:
        data = json.load(f)
    if not isinstance(data, dict):
        continue
    for sym, entries in data.items():
        csym = clean_symbol(sym)
        if csym not in all_entries:
            all_entries[csym] = []
        if isinstance(entries, list):
            for e in entries:
                if isinstance(e, dict) and e.get("trades", 0) > 100:
                    all_entries[csym].append(e)

# ── For each pair, find FLOOR (max trades), CEILING (max WR), KNEE (best PF) ──
results = {}

for csym, entries in all_entries.items():
    if not entries:
        continue

    pv = get_pip_value(csym)
    sp = SPREADS.get(csym, DEFAULT_SPREAD)

    # FLOOR = max trades
    floor_e = max(entries, key=lambda e: e.get("trades", 0))
    # CEILING = max WR (with at least some trades)
    valid_wr = [e for e in entries if e.get("trades", 0) > 50]
    ceiling_e = max(valid_wr, key=lambda e: e.get("wr", 0)) if valid_wr else None
    # KNEE = best PF with >300 trades, different from floor/ceiling
    valid_pf = [e for e in entries if e.get("trades", 0) > 300]
    knee_e = max(valid_pf, key=lambda e: e.get("pf", 0)) if valid_pf else None

    for label, entry in [("FLOOR", floor_e), ("CEILING", ceiling_e), ("KNEE", knee_e)]:
        if entry is None:
            continue
        trades = entry.get("trades", 0)
        wr = entry.get("wr", 0)
        gross_pnl = entry.get("pnl", 0)
        pf = entry.get("pf", 0)
        avg_w = entry.get("avg_w", 0)
        avg_l = entry.get("avg_l", 0)
        tr_d = entry.get("tr_per_day", 0)
        trigger = entry.get("t1_trigger", 0)

        gross_usd, sprd_usd, comm_usd, net_usd, cost_pct = calc_costs(
            trades, gross_pnl, sp, pv)

        key = csym + "_" + label
        results[key] = {
            "pair": csym, "mode": label, "trades": trades, "wr": wr,
            "pf": pf, "avg_w": avg_w, "avg_l": avg_l, "tr_per_day": tr_d,
            "trigger": trigger, "spread": sp,
            "gross_usd": gross_usd, "sprd_usd": sprd_usd,
            "comm_usd": comm_usd, "net_usd": net_usd, "cost_pct": cost_pct,
        }

# ── Print ──
for mode in ["FLOOR", "KNEE", "CEILING"]:
    mode_results = {k: v for k, v in results.items() if v["mode"] == mode}
    if not mode_results:
        continue

    print()
    print("=" * 85)
    print(mode + " BASKET")
    print("=" * 85)
    header = "Pair       Trades   WR%    PF    Tr/d   Gross$     Spread$   Comm$     Net$      Cost%"
    print(header)
    print("-" * 85)

    basket = {"trades": 0, "gross": 0, "sprd": 0, "comm": 0, "net": 0}

    for key in sorted(mode_results.keys()):
        r = mode_results[key]
        line = (
            r["pair"].ljust(10) + " " +
            str(r["trades"]).rjust(7) + " " +
            str(round(r["wr"], 1)).rjust(5) + "% " +
            str(round(r["pf"], 1)).rjust(5) + " " +
            str(round(r.get("tr_per_day", 0), 2)).rjust(5) + "  " +
            ("$" + str(round(r["gross_usd"], 2))).rjust(9) + " " +
            ("$" + str(round(r["sprd_usd"], 2))).rjust(7) + " " +
            ("$" + str(round(r["comm_usd"], 2))).rjust(7) + " " +
            ("$" + str(round(r["net_usd"], 2))).rjust(9) + " " +
            str(round(r["cost_pct"], 1)).rjust(5) + "%"
        )
        print(line)

        basket["trades"] += r["trades"]
        basket["gross"] += r["gross_usd"]
        basket["sprd"] += r["sprd_usd"]
        basket["comm"] += r["comm_usd"]
        basket["net"] += r["net_usd"]

    total_cost = basket["sprd"] + basket["comm"]
    cost_pct_total = total_cost / basket["gross"] * 100 if basket["gross"] > 0 else 0

    print("-" * 85)
    total_line = (
        "TOTAL".ljust(10) + " " +
        str(basket["trades"]).rjust(7) + " " +
        " " * 17 +
        ("$" + str(round(basket["gross"], 2))).rjust(9) + " " +
        ("$" + str(round(basket["sprd"], 2))).rjust(7) + " " +
        ("$" + str(round(basket["comm"], 2))).rjust(7) + " " +
        ("$" + str(round(basket["net"], 2))).rjust(9) + " " +
        str(round(cost_pct_total, 1)).rjust(5) + "%"
    )
    print(total_line)

print()
print("=" * 85)
print("ASSETS COVERED: " + str(len(set(v["pair"] for v in results.values()))) + " pairs")
print("SPREADS: Current MT5 | Commission: $0.07/round-turn")
print("=" * 85)
