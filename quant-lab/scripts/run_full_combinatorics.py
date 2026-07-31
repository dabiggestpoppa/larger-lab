"""
FULL UNIVERSE COMBINATORICS — FX + Crypto + Metals + Indices
==============================================================
MAD Directive 2026-06-06: Run once after all sweeps verified.
Sources:
  - Forex: reports/_matrix_data.pkl (FLOOR/CEILING/KNEE/BEST_NET/LOW_COST)
  - Crypto: reports/trigger_sweep_crypto.json
  - Metals/Indices: reports/trigger_sweep_metals_indices.json (just swept)
Output:
  - reports/GROUP_COMBINATORICS_FULL.md
"""

import json, os, pickle, math
from itertools import combinations
from collections import defaultdict

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

COMM = 0.07  # per round-turn commission

# ── Spread assumptions (pips) ────────────────────────────────────────────
SPREADS = {
    # FX majors
    "EURUSD": 0.20, "USDJPY": 0.20, "GBPUSD": 0.30, "USDCHF": 0.70,
    "AUDUSD": 0.30, "NZDUSD": 0.20, "USDCAD": 0.40,
    # FX crosses
    "EURGBP": 0.30, "EURJPY": 0.40, "GBPJPY": 1.00, "EURCHF": 0.50,
    "AUDJPY": 0.50, "NZDJPY": 0.60, "AUDNZD": 0.80, "AUDCAD": 0.60,
    "AUDCHF": 0.80, "CADJPY": 0.60, "CHFJPY": 1.40, "CADCHF": 1.00,
    "EURNZD": 1.20, "EURAUD": 0.80, "EURCAD": 0.70, "GBPAUD": 1.00,
    "GBPCAD": 0.80, "GBPCHF": 1.00, "GBPNZD": 1.50, "NZDCAD": 0.80,
    "NZDCHF": 1.00,
    # Crypto
    "BTCUSD": 35.0, "ETHUSD": 5.0,
    # Metals
    "XAUUSD": 3.0, "XAGUSD": 0.5,
    # Indices
    "US500": 0.5, "DE30": 2.0, "FR40": 1.5, "HK50": 3.0,
}

def get_spread(pair):
    return SPREADS.get(pair, 0.5)

def get_pip_val(pair):
    if pair in ("BTCUSD", "ETHUSD"):
        return 1.0
    if pair in ("XAUUSD", "XAGUSD"):
        return 0.1 if pair == "XAUUSD" else 0.01
    if pair in ("US500", "DE30", "FR40", "HK50"):
        return 1.0
    if "JPY" in pair:
        return 0.07
    return 0.10

def calc_net(entry, pair):
    """Convert raw sweep entry to standardized format with net USD etc."""
    trades = entry.get("trades", 0)
    wr = entry.get("wr", 0)
    pf = entry.get("pf", 0)
    pnl = entry.get("pnl", 0)
    tr_d = entry.get("tr_per_day", 0)
    trigger = entry.get("t1_trigger", 0)
    pval = get_pip_val(pair)
    spread = get_spread(pair)
    
    gross = pnl * pval
    sprd_cost = trades * spread * pval
    comm_cost = trades * COMM
    net = gross - sprd_cost - comm_cost
    cost_pct = (sprd_cost + comm_cost) / gross * 100 if gross > 0 else 999
    
    return {
        "trigger": trigger, "trades": trades, "wr": wr, "pf": pf,
        "tr_per_day": tr_d, "gross_usd": gross, "sprd_usd": sprd_cost,
        "comm_usd": comm_cost, "net_usd": net, "cost_pct": cost_pct,
        "spread": spread, "pnl": pnl,
    }

# ── Load Forex data ──────────────────────────────────────────────────────
print("Loading forex data from _matrix_data.pkl...")
with open(os.path.join(REPORTS_DIR, "_matrix_data.pkl"), "rb") as f:
    forex_data = pickle.load(f)

# ── Load Crypto sweep data ───────────────────────────────────────────────
print("Loading crypto sweep data...")
with open(os.path.join(REPORTS_DIR, "trigger_sweep_crypto.json")) as f:
    crypto_raw = json.load(f)

# ── Load Metals/Indices sweep data ───────────────────────────────────────
print("Loading metals/indices sweep data...")
with open(os.path.join(REPORTS_DIR, "trigger_sweep_metals_indices.json")) as f:
    metals_indices_raw = json.load(f)

# ── Build all_pairs dict ─────────────────────────────────────────────────
all_pairs = {}

# Add forex pairs with all operating points
for csym, data in forex_data.items():
    best_mode, best_net, best_e = None, -999999, None
    for mode in ["FLOOR", "CEILING", "KNEE", "BEST_NET", "LOW_COST"]:
        e = data.get(mode)
        if e and isinstance(e, dict) and e.get("net_usd", -999999) > best_net:
            best_net = e["net_usd"]
            best_mode = mode
            best_e = e.copy()
    if best_mode and best_e:
        best_e["mode"] = best_mode
        best_e["type"] = "FOREX"
        all_pairs[csym] = best_e

N_FOREX = len(all_pairs)
print(f"  Forex pairs: {N_FOREX}")

# Add crypto pairs — pick best entry from ceiling/floor sweep lists
for section_name, pairs_data in crypto_raw.items():
    mode_name = "FLOOR" if section_name == "floor" else "CEILING"
    if not isinstance(pairs_data, dict):
        continue
    for sym, entries in pairs_data.items():
        csym = sym.replace(".PRO", "").replace("_PRO", "")
        if not isinstance(entries, list):
            continue
        best_e = None
        best_net = -999999
        for e in entries:
            ne = calc_net(e, csym)
            ne["mode"] = mode_name
            ne["type"] = "CRYPTO"
            if ne["net_usd"] > best_net:
                best_net = ne["net_usd"]
                best_e = ne
        if best_e:
            if csym not in all_pairs or best_e["net_usd"] > all_pairs[csym].get("net_usd", -999999):
                all_pairs[csym] = best_e

N_CRYPTO = sum(1 for v in all_pairs.values() if v.get("type") == "CRYPTO")
print(f"  Crypto pairs: {N_CRYPTO}")

# Add metals/indices — pick best from our sweep using operating points
# From the sweep data, we pick: FLOOR = max trades, CEILING = max WR, KNEE = best PF
for asset_key, data in metals_indices_raw.items():
    floor_entries = data.get("floor", [])
    if not floor_entries:
        continue
    
    # FLOOR = entry with most trades
    floor_e = max(floor_entries, key=lambda e: e.get("trades", 0))
    floor_calc = calc_net(floor_e, asset_key)
    floor_calc["mode"] = "FLOOR"
    
    # CEILING = entry with highest WR (min 50 trades to avoid artifacts)
    valid_ceiling = [e for e in floor_entries if e.get("trades", 0) >= 50]
    if valid_ceiling:
        ceil_e = max(valid_ceiling, key=lambda e: e.get("wr", 0))
    else:
        ceil_e = max(floor_entries, key=lambda e: e.get("wr", 0))
    ceil_calc = calc_net(ceil_e, asset_key)
    ceil_calc["mode"] = "CEILING"
    
    # KNEE = entry with best PF ( WR >= 80% to avoid low-WR high-PF artifacts)
    valid_knee = [e for e in floor_entries if e.get("wr", 0) >= 80 and e.get("trades", 0) >= 50]
    if valid_knee:
        knee_e = max(valid_knee, key=lambda e: e.get("pf", 0))
    else:
        knee_e = max(floor_entries, key=lambda e: e.get("pf", 0))
    knee_calc = calc_net(knee_e, asset_key)
    knee_calc["mode"] = "KNEE"
    
    # Pick the best mode (highest net) and store all
    for calc, mode_name in [(floor_calc, "FLOOR"), (ceil_calc, "CEILING"), (knee_calc, "KNEE")]:
        calc["type"] = "METAL" if asset_key in ("XAUUSD", "XAGUSD") else "INDEX"
        calc["mode"] = mode_name
        if asset_key not in all_pairs or calc["net_usd"] > all_pairs[asset_key].get("net_usd", -999999):
            all_pairs[asset_key] = calc

N_METALS = sum(1 for v in all_pairs.values() if v.get("type") == "METAL")
N_INDICES = sum(1 for v in all_pairs.values() if v.get("type") == "INDEX")
print(f"  Metals: {N_METALS}")
print(f"  Indices: {N_INDICES}")
print(f"  TOTAL: {len(all_pairs)} pairs")

# ── Print individual pair stats ──────────────────────────────────────────
print("\n" + "=" * 110)
print("ALL PAIRS — BEST CONFIG SUMMARY")
print("=" * 110)
sorted_all = sorted(all_pairs.items(), key=lambda x: x[1]["net_usd"], reverse=True)

print(f"{'Pair':10s} {'Type':8s} {'Mode':10s} {'Trades':>7s} {'WR%':>6s} {'PF':>6s} {'Tr/d':>6s} {'Net$':>12s} {'Cost%':>6s} {'Sprd':>6s}")
print("-" * 110)
for csym, e in sorted_all:
    ptype = e.get("type", "?")
    print(f"{csym:10s} {ptype:8s} {e.get('mode',''):10s} {e['trades']:>7d} {e['wr']:>6.1f} {e['pf']:>6.1f} "
          f"{e.get('tr_per_day',0):>6.2f} ${e['net_usd']:>10.2f} {e['cost_pct']:>6.1f} {e.get('spread',0):>5.1f}p")

# ── Categorize ────────────────────────────────────────────────────────────
categories = {
    "MAX PROFIT (net > $3,000)": [],
    "SWEET SPOT (PF > 20, cost% < 15%)": [],
    "LOW COST (cost% < 10%)": [],
    "HIGH ACCURACY (WR > 85%)": [],
    "HIGH FREQUENCY (tr/d > 1.0)": [],
    "AVOID (cost% > 25%)": [],
    "METALS": [],
    "INDICES": [],
    "CRYPTO": [],
}

for csym, e in sorted_all:
    if e["net_usd"] > 3000:
        categories["MAX PROFIT (net > $3,000)"].append((csym, e))
    if e["pf"] > 20 and e["cost_pct"] < 15:
        categories["SWEET SPOT (PF > 20, cost% < 15%)"].append((csym, e))
    if e["cost_pct"] < 10:
        categories["LOW COST (cost% < 10%)"].append((csym, e))
    if e["wr"] > 85:
        categories["HIGH ACCURACY (WR > 85%)"].append((csym, e))
    if e.get("tr_per_day", 0) > 1.0:
        categories["HIGH FREQUENCY (tr/d > 1.0)"].append((csym, e))
    if e["cost_pct"] > 25:
        categories["AVOID (cost% > 25%)"].append((csym, e))
    if e.get("type") == "METAL":
        categories["METALS"].append((csym, e))
    elif e.get("type") == "INDEX":
        categories["INDICES"].append((csym, e))
    elif e.get("type") == "CRYPTO":
        categories["CRYPTO"].append((csym, e))

# ── Combinatorics ─────────────────────────────────────────────────────────
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
    modes = defaultdict(int)
    types = defaultdict(int)
    for _, d in combo:
        modes[d.get("mode", "?")] += 1
        types[d.get("type", "?")] += 1
    mode_str = ", ".join(f"{v}x {k}" for k, v in sorted(modes.items()))
    type_str = ", ".join(f"{k}:{v}" for k, v in sorted(types.items()))
    return {
        "net": total_net, "trades": total_trades, "gross": total_gross,
        "cost_usd": total_cost, "avg_wr": avg_wr, "avg_pf": avg_pf,
        "avg_cost_pct": avg_cost_pct, "tr_per_day": total_tr_d,
        "mode_str": mode_str, "type_str": type_str,
    }

def greedy_top3(pairs_list, size, key_fn, reverse=True, filter_fn=None):
    flist = [p for p in pairs_list if (filter_fn is None or filter_fn(p))]
    slist = sorted(flist, key=key_fn, reverse=reverse)
    results = []
    used_sets = set()
    for seed_idx in range(min(15, len(slist))):
        combo = [slist[seed_idx]]
        used = {slist[seed_idx][0]}
        for _ in range(size - 1):
            best_next, best_score = None, (-9999999 if reverse else 9999999)
            for p in slist:
                if p[0] in used or (filter_fn and not filter_fn(p)):
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

# ── Generate output ──────────────────────────────────────────────────────
O = []
O.append("=" * 120)
O.append("FULL UNIVERSE COMBINATORICS — FX + CRYPTO + METALS + INDICES")
O.append("=" * 120)
O.append(f"Total pairs: {len(all_pairs)} ({N_FOREX} forex + {N_CRYPTO} crypto + {N_METALS} metals + {N_INDICES} indices)")
O.append(f"Operating points: FLOOR, CEILING, KNEE (best config selected per pair)")
O.append("")

# Rankings
O.append("=" * 120)
O.append("RANKINGS — ALL PAIRS BY NET PROFIT (best config per pair)")
O.append("=" * 120)
for i, (csym, e) in enumerate(sorted_all, 1):
    ptype = e.get("type", "?")
    O.append(f"  {i:>3}. {csym:10s} {ptype:8s} {e.get('mode',''):10s} "
             f"Net: ${e['net_usd']:>10.2f} | WR: {e['wr']:.1f}% | PF: {e['pf']:.1f} | "
             f"Cost: {e['cost_pct']:.1f}% | Tr/d: {e.get('tr_per_day',0):.2f} | Sprd: {e.get('spread',0):.1f}p")

# Categories per asset
O.append("")
O.append("=" * 120)
O.append("CATEGORIES — PAIRS BY STRENGTH")
O.append("=" * 120)
for cat, items in categories.items():
    O.append(f"\n--- {cat} ({len(items)} pairs) ---")
    if items:
        for csym, e in sorted(items, key=lambda x: x[1]["net_usd"], reverse=True):
            O.append(f"  {csym:10s} {e.get('type',''):8s} Net: ${e['net_usd']:>10.2f} | "
                     f"WR: {e['wr']:.1f}% | PF: {e['pf']:.1f} | Cost: {e['cost_pct']:.1f}%")
    else:
        O.append("  (none)")

# Group combinatorics
plist = list(all_pairs.items())

O.append("")
O.append("")
O.append("=" * 120)
O.append("OPTIMAL BASKETS — TOP 3 PER CATEGORY AT EACH SIZE (2-14 assets)")
O.append("=" * 120)

for size in range(2, min(15, len(plist) + 1)):
    gname = GROUP_NAMES.get(size, f"{size}-SETS")
    O.append("")
    O.append("=" * 120)
    O.append(f"{gname} ({size} ASSETS)")
    O.append("=" * 120)

    cats = [
        ("MAX PROFIT", lambda p: p[1]["net_usd"], True, None),
        ("LOW COST", lambda p: p[1]["cost_pct"], False, None),
        ("HIGH ACCURACY", lambda p: p[1]["wr"], True, None),
        ("HIGH FREQUENCY", lambda p: p[1].get("tr_per_day", 0), True, None),
        ("SWEET SPOT", lambda p: p[1]["pf"], True,
         lambda p: p[1]["pf"] > 15 and p[1]["cost_pct"] < 20),
    ]

    for cat_name, key_fn, rev, filt_fn in cats:
        O.append(f"\n  [{cat_name}]")
        O.append("  " + "-" * 105)
        top3 = greedy_top3(plist, size, key_fn, reverse=rev, filter_fn=filt_fn)
        if not top3:
            O.append("    (no combo meets criteria)")
        for rank, combo in enumerate(top3, 1):
            m = basket_metrics(combo)
            pairs_str = ", ".join(f"{c[0]}({c[1].get('mode','')})" for c in combo)
            O.append(f"    #{rank} Net: ${m['net']:>12.2f} | Avg WR: {m['avg_wr']:.1f}% | "
                     f"Avg PF: {m['avg_pf']:.1f} | Cost: {m['avg_cost_pct']:.1f}% | "
                     f"Trades: {m['trades']:>6d} | Tr/d: {m['tr_per_day']:.2f}")
            O.append(f"        Types: {m['type_str']} | Modes: {m['mode_str']}")
            O.append(f"        {pairs_str}")

# MAD's strategy
O.append("")
O.append("")
O.append("=" * 120)
O.append("MAD'S STRATEGY — LOW COST UNTIL $250, THEN MAX PROFIT")
O.append("=" * 120)

O.append("\n--- PHASE 1: LOW COST GROUPS (build to $250) ---")
for size in range(2, min(15, len(plist) + 1)):
    gname = GROUP_NAMES.get(size, f"{size}-SETS")
    top3 = greedy_top3(plist, size, lambda p: p[1]["cost_pct"], reverse=False)
    if top3:
        m = basket_metrics(top3[0])
        pairs_str = ", ".join(f"{c[0]}({c[1].get('mode','')})" for c in top3[0])
        O.append(f"  {gname:14s} Net: ${m['net']:>12.2f} | Cost: {m['avg_cost_pct']:.1f}% | "
                 f"WR: {m['avg_wr']:.1f}% | Trades: {m['trades']:>6d}")
        O.append(f"    {pairs_str}")

O.append("\n--- PHASE 2: MAX PROFIT GROUPS (at $250+) ---")
for size in range(2, min(15, len(plist) + 1)):
    gname = GROUP_NAMES.get(size, f"{size}-SETS")
    top3 = greedy_top3(plist, size, lambda p: p[1]["net_usd"], reverse=True)
    if top3:
        m = basket_metrics(top3[0])
        pairs_str = ", ".join(f"{c[0]}({c[1].get('mode','')})" for c in top3[0])
        O.append(f"  {gname:14s} Net: ${m['net']:>12.2f} | Cost: {m['avg_cost_pct']:.1f}% | "
                 f"WR: {m['avg_wr']:.1f}% | Trades: {m['trades']:>6d}")
        O.append(f"    {pairs_str}")

O.append("")
O.append("=" * 120)
O.append("END OF FULL UNIVERSE COMBINATORICS")
O.append("=" * 120)

result = "\n".join(O)
print(result)

output_path = os.path.join(REPORTS_DIR, "GROUP_COMBINATORICS_FULL.md")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(result)
print(f"\n\nSaved to: {output_path}")
