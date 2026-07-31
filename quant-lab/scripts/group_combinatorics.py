"""
GROUP COMBINATORICS — Top 3 Duos, Trios, Quads, Hex, etc.
For each group size (2-14), find top 3 by 5 categories.
"""

import json, os, pickle
from collections import defaultdict

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")

with open(os.path.join(REPORTS_DIR, "_matrix_data.pkl"), "rb") as f:
    forex_results = pickle.load(f)

with open(os.path.join(REPORTS_DIR, "trigger_sweep_crypto.json")) as f:
    crypto_raw = json.load(f)

COMM = 0.07
SPREADS = {
    "EURUSD": 0.20, "USDJPY": 0.20, "CHFJPY": 1.40,
    "NZDUSD": 0.20, "AUDUSD": 0.30, "USDCHF": 0.70, "GBPJPY": 1.00,
    "BTCUSD": 35.0, "ETHUSD": 5.0,
}
DEFAULT_SPREAD = 0.50

def pv(pair):
    return 1.0 if pair in ("BTCUSD", "ETHUSD") else (0.07 if "JPY" in pair else 0.10)

def sp(pair):
    return SPREADS.get(pair, DEFAULT_SPREAD)

def calc(e, pair):
    trades = e.get("trades", 0)
    wr = e.get("wr", 0)
    pf = e.get("pf", 0)
    pnl = e.get("pnl", 0)
    tr_d = e.get("tr_per_day", 0)
    trigger = e.get("t1_trigger", 0)
    pval = pv(pair)
    spread = sp(pair)
    gross = pnl * pval
    sprd_c = trades * spread * pval
    comm_c = trades * COMM
    net = gross - sprd_c - comm_c
    cost_pct = (sprd_c + comm_c) / gross * 100 if gross > 0 else 999
    return {"trigger": trigger, "trades": trades, "wr": wr, "pf": pf,
            "tr_per_day": tr_d, "gross_usd": gross, "sprd_usd": sprd_c,
            "comm_usd": comm_c, "net_usd": net, "cost_pct": cost_pct, "spread": spread}

# Build best config per pair
all_pairs = {}

for csym, data in forex_results.items():
    best_mode, best_net, best_e = None, -999999, None
    for mode in ["FLOOR", "CEILING", "KNEE", "BEST_NET", "LOW_COST"]:
        e = data.get(mode)
        if e and e.get("net_usd", -999999) > best_net:
            best_net = e["net_usd"]
            best_mode = mode
            best_e = e.copy()
    if best_mode:
        best_e["mode"] = best_mode
        best_e["type"] = "FOREX"
        all_pairs[csym] = best_e

for section_name, pairs_data in crypto_raw.items():
    mode = "FLOOR" if section_name == "floor" else "CEILING"
    for sym, entries in pairs_data.items():
        csym = sym.replace(".PRO", "").replace("_PRO", "")
        if not isinstance(entries, list):
            continue
        for e in entries:
            ne = calc(e, csym)
            ne["mode"] = mode
            ne["type"] = "CRYPTO"
            if csym not in all_pairs or ne["net_usd"] > all_pairs[csym]["net_usd"]:
                all_pairs[csym] = ne

# Sort by net profit
sorted_pairs = sorted(all_pairs.items(), key=lambda x: x[1]["net_usd"], reverse=True)

GROUP_NAMES = {
    2: "DUOS", 3: "TRIOS", 4: "QUADS", 5: "QUINTS",
    6: "HEX", 7: "SEPTS", 8: "OCTS", 9: "NONS",
    10: "DECS", 11: "UNDECS", 12: "DUODECS", 13: "TREDECS", 14: "QUATTORDECS"
}

def basket_metrics(combo):
    total_net = sum(d["net_usd"] for _, d in combo)
    total_trades = sum(d["trades"] for _, d in combo)
    total_gross = sum(d["gross_usd"] for _, d in combo)
    total_cost = sum(d["sprd_usd"] + d["comm_usd"] for _, d in combo)
    avg_wr = sum(d["wr"] for _, d in combo) / len(combo)
    avg_pf = sum(d["pf"] for _, d in combo) / len(combo)
    avg_cost_pct = total_cost / total_gross * 100 if total_gross > 0 else 999
    total_tr_d = sum(d.get("tr_per_day", 0) for _, d in combo)
    modes = {}
    for _, d in combo:
        m = d["mode"]
        modes[m] = modes.get(m, 0) + 1
    mode_str = ", ".join(str(v) + "x " + k for k, v in sorted(modes.items()))
    fx = sum(1 for _, d in combo if d["type"] == "FOREX")
    cr = sum(1 for _, d in combo if d["type"] == "CRYPTO")
    return {"net": total_net, "trades": total_trades, "gross": total_gross,
            "cost_usd": total_cost, "avg_wr": avg_wr, "avg_pf": avg_pf,
            "avg_cost_pct": avg_cost_pct, "tr_per_day": total_tr_d,
            "mode_str": mode_str, "fx": fx, "cr": cr}

def greedy_top3(pairs_list, size, key_fn, reverse=True, filter_fn=None):
    """Greedy top-3. key_fn and filter_fn receive (csym, data) tuples."""
    flist = [p for p in pairs_list if (filter_fn is None or filter_fn(p))]
    slist = sorted(flist, key=key_fn, reverse=reverse)
    results = []
    used_sets = set()
    for seed_idx in range(min(10, len(slist))):
        combo = [slist[seed_idx]]
        used = {slist[seed_idx][0]}
        for _ in range(size - 1):
            best_next, best_score = None, (-999999 if reverse else 999999)
            for p in slist:
                if p[0] in used:
                    continue
                if filter_fn and not filter_fn(p):
                    continue
                score = key_fn(p)
                if (reverse and score > best_score) or (not reverse and score < best_score):
                    best_score = score
                    best_next = p
            if best_next:
                combo.append(best_next)
                used.add(best_next[0])
        if len(combo) == size:
            key = frozenset(c[0] for c in combo)
            if key not in used_sets:
                used_sets.add(key)
                results.append(combo)
        if len(results) >= 3:
            break
    return results

O = []
O.append("=" * 110)
O.append("GROUP COMBINATORICS — TOP 3 PER CATEGORY AT EACH SIZE (2-14)")
O.append("=" * 110)
O.append("Using best config per pair from sweep data.")
O.append("")

plist = list(all_pairs.items())

for size in range(2, 15):
    if size > len(plist):
        break
    gname = GROUP_NAMES.get(size, str(size) + "-SETS")
    O.append("")
    O.append("=" * 110)
    O.append(gname + " (" + str(size) + " ASSETS)")
    O.append("=" * 110)

    cats = [
        ("MAX PROFIT", lambda p: p[1]["net_usd"], True, None),
        ("LOW COST", lambda p: p[1]["cost_pct"], False, None),
        ("HIGH ACCURACY", lambda p: p[1]["wr"], True, None),
        ("HIGH FREQUENCY", lambda p: p[1].get("tr_per_day", 0), True, None),
        ("SWEET SPOT", lambda p: p[1]["pf"], True, lambda p: p[1]["pf"] > 15 and p[1]["cost_pct"] < 20),
    ]

    for cat_idx, (cat_name, key_fn, rev, filt_fn) in enumerate(cats, 1):
        O.append("")
        O.append("  [" + str(cat_idx) + "] " + cat_name)
        O.append("  " + "-" * 100)
        top3 = greedy_top3(plist, size, key_fn, reverse=rev, filter_fn=filt_fn)
        if not top3:
            O.append("    (no combo meets criteria at this size)")
        for rank, combo in enumerate(top3, 1):
            m = basket_metrics(combo)
            pairs_str = ", ".join(c[0] + "(" + c[1]["mode"] + ")" for c in combo)
            O.append(
                "    #" + str(rank) + " Net: $" + str(round(m["net"], 2)).rjust(12) +
                " | Avg WR: " + str(round(m["avg_wr"], 1)) + "%" +
                " | Avg PF: " + str(round(m["avg_pf"], 1)) +
                " | Cost: " + str(round(m["avg_cost_pct"], 1)) + "%" +
                " | Trades: " + str(m["trades"]).rjust(6) +
                " | FX:" + str(m["fx"]) + " CR:" + str(m["cr"])
            )
            O.append("        " + pairs_str)

# MAD'S STRATEGY
O.append("")
O.append("")
O.append("=" * 110)
O.append("MAD'S STRATEGY — LOW COST UNTIL $250, THEN MAX PROFIT")
O.append("=" * 110)
O.append("")
O.append("Phase 1 (Current): LOW COST groups — build to $250 account")
O.append("Phase 2 (At $250): Switch to MAX PROFIT groups")
O.append("")

O.append("--- PHASE 1: LOW COST GROUPS (build to $250) ---")
O.append("")
for size in range(2, 15):
    if size > len(plist):
        break
    gname = GROUP_NAMES.get(size, str(size) + "-SETS")
    top3 = greedy_top3(plist, size, lambda p: p[1]["cost_pct"], reverse=False)
    if top3:
        m = basket_metrics(top3[0])
        pairs_str = ", ".join(c[0] + "(" + c[1]["mode"] + ")" for c in top3[0])
        O.append("  " + gname.ljust(14) + " Net: $" + str(round(m["net"], 2)).rjust(12) +
                 " | Cost: " + str(round(m["avg_cost_pct"], 1)) + "%" +
                 " | Avg WR: " + str(round(m["avg_wr"], 1)) + "%" +
                 " | Trades: " + str(m["trades"]).rjust(6))
        O.append("    " + pairs_str)

O.append("")
O.append("--- PHASE 2: MAX PROFIT GROUPS (at $250+) ---")
O.append("")
for size in range(2, 15):
    if size > len(plist):
        break
    gname = GROUP_NAMES.get(size, str(size) + "-SETS")
    top3 = greedy_top3(plist, size, lambda p: p[1]["net_usd"], reverse=True)
    if top3:
        m = basket_metrics(top3[0])
        pairs_str = ", ".join(c[0] + "(" + c[1]["mode"] + ")" for c in top3[0])
        O.append("  " + gname.ljust(14) + " Net: $" + str(round(m["net"], 2)).rjust(12) +
                 " | Cost: " + str(round(m["avg_cost_pct"], 1)) + "%" +
                 " | Avg WR: " + str(round(m["avg_wr"], 1)) + "%" +
                 " | Trades: " + str(m["trades"]).rjust(6))
        O.append("    " + pairs_str)

# PLUG & PLAY
O.append("")
O.append("")
O.append("=" * 110)
O.append("PLUG & PLAY REFERENCE — QUICK LOOKUP BY GROUP SIZE")
O.append("=" * 110)
O.append("")
O.append("For prop firms / multiple accounts: pick a group size, pick a category, go.")
O.append("")

for size in range(2, 15):
    if size > len(plist):
        break
    gname = GROUP_NAMES.get(size, str(size) + "-SETS")
    bp = greedy_top3(plist, size, lambda p: p[1]["net_usd"], reverse=True)
    bc = greedy_top3(plist, size, lambda p: p[1]["cost_pct"], reverse=False)
    ba = greedy_top3(plist, size, lambda p: p[1]["wr"], reverse=True)
    bs = greedy_top3(plist, size, lambda p: p[1]["pf"], reverse=True,
                      filter_fn=lambda p: p[1]["pf"] > 15 and p[1]["cost_pct"] < 20)

    O.append(gname + " (" + str(size) + " assets):")
    if bp:
        m = basket_metrics(bp[0])
        O.append("  MAX PROFIT:  $" + str(round(m["net"], 2)).rjust(12) + " | " +
                 ", ".join(c[0] + "(" + c[1]["mode"] + ")" for c in bp[0]))
    if bc:
        m = basket_metrics(bc[0])
        O.append("  LOW COST:    $" + str(round(m["net"], 2)).rjust(12) + " | " +
                 ", ".join(c[0] + "(" + c[1]["mode"] + ")" for c in bc[0]))
    if ba:
        m = basket_metrics(ba[0])
        O.append("  HIGH ACC:    $" + str(round(m["net"], 2)).rjust(12) + " | " +
                 ", ".join(c[0] + "(" + c[1]["mode"] + ")" for c in ba[0]))
    if bs:
        m = basket_metrics(bs[0])
        O.append("  SWEET SPOT:  $" + str(round(m["net"], 2)).rjust(12) + " | " +
                 ", ".join(c[0] + "(" + c[1]["mode"] + ")" for c in bs[0]))
    O.append("")

O.append("=" * 110)
O.append("END OF GROUP COMBINATORICS")
O.append("=" * 110)

result = "\n".join(O)
print(result)

with open(os.path.join(REPORTS_DIR, "GROUP_COMBINATORICS.md"), "w") as f:
    f.write(result)
print("\nSaved to reports/GROUP_COMBINATORICS.md")
