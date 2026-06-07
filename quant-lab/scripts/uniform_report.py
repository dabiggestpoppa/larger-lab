"""
Uniform FLOOR/KNEE/CEILING report for ALL metals & indices.
Velocity-focused combinatorics.
"""
import sys, json, os, pickle, math
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
COMM = 0.07

SPREADS = {
    "EURUSD": 0.20, "USDJPY": 0.20, "GBPUSD": 0.30, "USDCHF": 0.70,
    "AUDUSD": 0.30, "NZDUSD": 0.20, "USDCAD": 0.40,
    "EURGBP": 0.30, "EURJPY": 0.40, "GBPJPY": 1.00, "EURCHF": 0.50,
    "AUDJPY": 0.50, "NZDJPY": 0.60, "AUDNZD": 0.80, "AUDCAD": 0.60,
    "AUDCHF": 0.80, "CADJPY": 0.60, "CHFJPY": 1.40, "CADCHF": 1.00,
    "EURNZD": 1.20, "EURAUD": 0.80, "EURCAD": 0.70, "GBPAUD": 1.00,
    "GBPCAD": 0.80, "GBPCHF": 1.00, "GBPNZD": 1.50, "NZDCAD": 0.80,
    "NZDCHF": 1.00,
    "BTCUSD": 35.0, "ETHUSD": 5.0,
    "XAUUSD": 3.0, "XAGUSD": 0.5,
    "US500": 0.5, "DE30": 2.0, "FR40": 1.5, "HK50": 3.0,
}

def get_spread(pair): return SPREADS.get(pair, 0.5)
def get_pip_val(pair):
    if pair in ("BTCUSD","ETHUSD"): return 1.0
    if pair == "XAUUSD": return 0.1
    if pair == "XAGUSD": return 0.01
    if pair in ("US500","DE30","FR40","HK50"): return 1.0
    if "JPY" in pair: return 0.07
    return 0.10

def calc_net(entry, pair):
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

# Load all data
with open(os.path.join(REPORTS_DIR, "_matrix_data.pkl"), "rb") as f:
    forex_data = pickle.load(f)
with open(os.path.join(REPORTS_DIR, "trigger_sweep_crypto.json")) as f:
    crypto_raw = json.load(f)
with open(os.path.join(REPORTS_DIR, "trigger_sweep_metals_indices.json")) as f:
    metals_indices_raw = json.load(f)

# UNIFORM TABLE for metals/indices
print("=" * 130)
print("UNIFORM SWEEP RESULTS -- METALS & INDICES")
print("=" * 130)

for asset_key in ["XAUUSD", "XAGUSD", "US500", "DE30", "FR40", "HK50"]:
    entries = metals_indices_raw.get(asset_key, {}).get("floor", [])
    if not entries:
        print(f"\n{asset_key}: NO DATA")
        continue

    pval = get_pip_val(asset_key)
    spread = get_spread(asset_key)

    # FLOOR = max trades
    floor_e = max(entries, key=lambda e: e.get("trades", 0))
    # CEILING = max WR (min 50 trades)
    valid_ceil = [e for e in entries if e.get("trades", 0) >= 50]
    ceil_e = max(valid_ceil, key=lambda e: e.get("wr", 0)) if valid_ceil else max(entries, key=lambda e: e.get("wr", 0))
    # KNEE = best PF (WR >= 80%, min 50 trades)
    valid_knee = [e for e in entries if e.get("wr", 0) >= 80 and e.get("trades", 0) >= 50]
    knee_e = max(valid_knee, key=lambda e: e.get("pf", 0)) if valid_knee else max(entries, key=lambda e: e.get("pf", 0))
    # BEST_NET = highest net USD
    net_entries = [(e, calc_net(e, asset_key)) for e in entries]
    best_net_e, best_net_calc = max(net_entries, key=lambda x: x[1]["net_usd"])

    print(f"\n  {asset_key}  |  pip_value=${pval}  |  spread={spread}p  |  data={entries[0]['days']} days")
    print("  " + "-" * 110)
    print(f"  {'Mode':10s} {'Mult':>6s} {'Trigger':>8s} {'Trades':>7s} {'WR%':>6s} {'PF':>6s} {'Tr/d':>6s} {'Net$':>12s} {'Cost%':>6s} {'Pnl':>10s}")
    print("  " + "-" * 110)

    for label, e in [("FLOOR", floor_e), ("KNEE", knee_e), ("CEILING", ceil_e), ("BEST_NET", best_net_e)]:
        c = calc_net(e, asset_key)
        print(f"  {label:10s} {e['multiplier']:>6.1f} {e['t1_trigger']:>8.1f} {e['trades']:>7d} {e['wr']:>6.1f} {e['pf']:>6.1f} {e['tr_per_day']:>6.2f} ${c['net_usd']:>10.2f} {c['cost_pct']:>6.1f} {e['pnl']:>10.1f}")

# Build all_pairs for combinatorics
all_pairs = {}
for csym, data in forex_data.items():
    best_mode, best_net, best_e = None, -999999, None
    for mode in ["FLOOR", "CEILING", "KNEE", "BEST_NET", "LOW_COST"]:
        e = data.get(mode)
        if e and isinstance(e, dict) and e.get("net_usd", -999999) > best_net:
            best_net = e["net_usd"]; best_mode = mode; best_e = e.copy()
    if best_mode and best_e:
        best_e["mode"] = best_mode; best_e["type"] = "FOREX"
        all_pairs[csym] = best_e

for section_name, pairs_data in crypto_raw.items():
    mode_name = "FLOOR" if section_name == "floor" else "CEILING"
    if not isinstance(pairs_data, dict): continue
    for sym, entries in pairs_data.items():
        csym = sym.replace(".PRO","").replace("_PRO","")
        if not isinstance(entries, list): continue
        best_e = None; best_net = -999999
        for e in entries:
            ne = calc_net(e, csym); ne["mode"] = mode_name; ne["type"] = "CRYPTO"
            if ne["net_usd"] > best_net: best_net = ne["net_usd"]; best_e = ne
        if best_e:
            if csym not in all_pairs or best_e["net_usd"] > all_pairs[csym].get("net_usd", -999999):
                all_pairs[csym] = best_e

for asset_key, data in metals_indices_raw.items():
    floor_entries = data.get("floor", [])
    if not floor_entries: continue
    best_e = None; best_net = -999999
    for e in floor_entries:
        ne = calc_net(e, asset_key)
        ne["type"] = "METAL" if asset_key in ("XAUUSD","XAGUSD") else "INDEX"
        ne["mode"] = "FLOOR"
        if ne["net_usd"] > best_net: best_net = ne["net_usd"]; best_e = ne
    if best_e:
        if asset_key not in all_pairs or best_e["net_usd"] > all_pairs[asset_key].get("net_usd", -999999):
            all_pairs[asset_key] = best_e

# Compute net/day
for csym, e in all_pairs.items():
    days = 1599
    e["net_per_day"] = e["net_usd"] / days
    e["tr_per_day"] = e.get("tr_per_day", 0)

# Velocity filter
velocity_pairs = {k: v for k, v in all_pairs.items() if v.get("tr_per_day", 0) >= 2.0}
slow_pairs = {k: v for k, v in all_pairs.items() if v.get("tr_per_day", 0) < 2.0}

print(f"\n\n{'='*130}")
print("VELOCITY ANALYSIS")
print(f"{'='*130}")
print(f"\nPairs with >= 2 tr/day: {len(velocity_pairs)}")
print(f"Pairs with < 2 tr/day: {len(slow_pairs)}")
print(f"\nSlow pairs (excluded from multi-asset combos):")
for csym, e in sorted(slow_pairs.items(), key=lambda x: x[1].get("tr_per_day", 0), reverse=True):
    print(f"  {csym:10s} tr/d={e.get('tr_per_day',0):.2f}  WR={e['wr']:.1f}%  PF={e['pf']:.1f}  Net=${e['net_usd']:.0f}")

# Velocity rankings
print(f"\n{'='*130}")
print("VELOCITY RANKINGS -- By Net/Day (return per day)")
print(f"{'='*130}")
by_velocity = sorted(all_pairs.items(), key=lambda x: x[1]["net_per_day"], reverse=True)
print(f"{'#':>3s} {'Pair':10s} {'Type':8s} {'Mode':10s} {'Tr/d':>6s} {'Net/day':>10s} {'Net total':>12s} {'WR%':>6s} {'PF':>6s} {'Cost%':>6s}")
print("-" * 100)
for i, (csym, e) in enumerate(by_velocity, 1):
    print(f"{i:>3d} {csym:10s} {e.get('type',''):8s} {e.get('mode',''):10s} {e.get('tr_per_day',0):>6.2f} ${e['net_per_day']:>9.2f} ${e['net_usd']:>11.2f} {e['wr']:>6.1f} {e['pf']:>6.1f} {e['cost_pct']:>6.1f}")

# Multi-asset combos using ONLY velocity pairs
print(f"\n\n{'='*130}")
print("MULTI-ASSET COMBOS -- Velocity pairs only (>= 2 tr/day)")
print(f"{'='*130}")

GROUP_NAMES = {2:"DUOS",3:"TRIOS",4:"QUADS",5:"QUINTS",6:"HEX",7:"SEPTS",8:"OCTS",9:"NONS",10:"DECS"}

def basket_metrics(combo):
    total_net = sum(d["net_usd"] for _, d in combo)
    total_trades = sum(d["trades"] for _, d in combo)
    total_gross = sum(d["gross_usd"] for _, d in combo)
    total_cost = sum(d["sprd_usd"] + d["comm_usd"] for _, d in combo)
    avg_wr = sum(d["wr"] for _, d in combo) / len(combo)
    avg_pf = sum(d["pf"] for _, d in combo) / len(combo)
    avg_cost_pct = total_cost / total_gross * 100 if total_gross > 0 else 999
    total_tr_d = sum(d.get("tr_per_day", 0) for _, d in combo)
    net_per_day = total_net / 1599
    types = defaultdict(int)
    for _, d in combo: types[d.get("type","?")] += 1
    type_str = ", ".join(f"{k}:{v}" for k, v in sorted(types.items()))
    return {"net": total_net, "trades": total_trades, "avg_wr": avg_wr, "avg_pf": avg_pf,
            "avg_cost_pct": avg_cost_pct, "tr_per_day": total_tr_d, "net_per_day": net_per_day, "type_str": type_str}

def greedy_top3(pairs_list, size, key_fn, reverse=True, filter_fn=None):
    flist = [p for p in pairs_list if (filter_fn is None or filter_fn(p))]
    slist = sorted(flist, key=key_fn, reverse=reverse)
    results = []; used_sets = set()
    for seed_idx in range(min(15, len(slist))):
        combo = [slist[seed_idx]]; used = {slist[seed_idx][0]}
        for _ in range(size - 1):
            best_next, best_score = None, (-9999999 if reverse else 9999999)
            for p in slist:
                if p[0] in used or (filter_fn and not filter_fn(p)): continue
                score = key_fn(p)
                if (reverse and score > best_score) or (not reverse and score < best_score):
                    best_score = score; best_next = p
            if best_next: combo.append(best_next); used.add(best_next[0])
        if len(combo) == size:
            key = frozenset(c[0] for c in combo)
            if key not in used_sets: used_sets.add(key); results.append(combo)
        if len(results) >= 3: break
    return results

pv_list = list(velocity_pairs.items())

for size in range(2, min(15, len(pv_list)+1)):
    gname = GROUP_NAMES.get(size, f"{size}-SETS")
    print(f"\n{'~'*130}")
    print(f"{gname} ({size} assets) -- all pairs >= 2 tr/day")
    print(f"{'~'*130}")

    for cat_name, key_fn, rev in [
        ("MAX VELOCITY (net/day)", lambda p: p[1]["net_per_day"], True),
        ("MAX NET TOTAL", lambda p: p[1]["net_usd"], True),
        ("HIGH FREQUENCY", lambda p: p[1].get("tr_per_day", 0), True),
    ]:
        top3 = greedy_top3(pv_list, size, key_fn, reverse=rev)
        print(f"\n  [{cat_name}]")
        if not top3:
            print("    (no combos)")
        for rank, combo in enumerate(top3, 1):
            m = basket_metrics(combo)
            pairs_str = ", ".join(f"{c[0]}({c[1].get('mode','')})" for c in combo)
            print(f"    #{rank} Net/day: ${m['net_per_day']:>10.2f} | Net total: ${m['net']:>12.2f} | "
                  f"Tr/d: {m['tr_per_day']:>6.1f} | Avg WR: {m['avg_wr']:.1f}% | Avg PF: {m['avg_pf']:.1f} | "
                  f"Cost: {m['avg_cost_pct']:.1f}%")
            print(f"        {m['type_str']}")
            print(f"        {pairs_str}")

# Single-asset velocity leaders
print(f"\n\n{'='*130}")
print("SINGLE ASSET VELOCITY -- Best net/day standalone")
print(f"{'='*130}")
for i, (csym, e) in enumerate(by_velocity[:10], 1):
    print(f"  {i:>2}. {csym:10s} {e.get('type',''):8s} {e.get('mode',''):10s}  "
          f"Net/day: ${e['net_per_day']:>10.2f} | Tr/d: {e.get('tr_per_day',0):.2f} | "
          f"WR: {e['wr']:.1f}% | PF: {e['pf']:.1f} | Cost: {e['cost_pct']:.1f}%")

print(f"\n{'='*130}")
print("END")
print(f"{'='*130}")
