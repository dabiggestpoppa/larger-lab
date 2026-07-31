"""
CEREBUS Velocity Optimizer v1.1 — FIXED
=========================================
Bug fixes:
  1. Crypto: keep best entry across ALL sections (floor+ceiling), not just last
  2. Forex: use the pkl data as-is (it's already net_usd correct)
  3. Metals/Indices: keep best per asset across all operating points
  4. Report: show which operating point was selected for each asset
"""
import sys, json, os, pickle
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
COMM = 0.07

PIP_VALUES = {
    "BTCUSD": 1.0, "ETHUSD": 1.0,
    "XAUUSD": 0.10, "XAGUSD": 0.10,
    "US500": 1.0, "DE30": 1.0, "FR40": 1.0, "HK50": 1.0,
}
DEFAULT_PIP = 0.10

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

def pip_val(pair): return PIP_VALUES.get(pair, DEFAULT_PIP)
def get_spread(pair): return SPREADS.get(pair, 0.5)

def calc_net_usd(entry, pair):
    """Calculate net USD from raw sweep entry."""
    trades = entry.get("trades", 0)
    pnl_pips = entry.get("pnl", 0)
    pval = pip_val(pair)
    spread = get_spread(pair)
    gross = pnl_pips * pval
    sprd_cost = trades * spread * pval
    comm_cost = trades * COMM
    net = gross - sprd_cost - comm_cost
    cost_pct = (sprd_cost + comm_cost) / gross * 100 if gross > 0 else 999
    return net, gross, cost_pct

def make_std(entry, pair, days, mode, atype):
    """Create standardized entry."""
    net, gross, cost_pct = calc_net_usd(entry, pair)
    trades = entry.get("trades", 0)
    wr = entry.get("wr", 0)
    pf = entry.get("pf", 0)
    tr_per_day = trades / days if days > 0 else 0
    net_per_day = net / days if days > 0 else 0
    return {
        "trades": trades, "wr": wr, "pf": pf,
        "net_usd": net, "gross_usd": gross, "cost_pct": cost_pct,
        "tr_per_day": tr_per_day, "net_per_day": net_per_day,
        "mode": mode, "type": atype, "days": days,
        "trigger": entry.get("t1_trigger", 0),
        "multiplier": entry.get("multiplier", 0),
        "annualized": net / days * 365 if days > 0 else 0,
    }

# ── LOAD DATA ─────────────────────────────────────────────────────────────
with open(os.path.join(REPORTS_DIR, "_matrix_data.pkl"), "rb") as f:
    forex_pkl = pickle.load(f)
with open(os.path.join(REPORTS_DIR, "trigger_sweep_crypto.json")) as f:
    crypto_json = json.load(f)
with open(os.path.join(REPORTS_DIR, "trigger_sweep_metals_indices.json")) as f:
    mi_json = json.load(f)

# ── PROCESS FOREX (from pkl — already has net_usd computed) ──────────────
all_assets = {}
for csym, modes in forex_pkl.items():
    pval = 0.07 if "JPY" in csym else 0.10
    best = None
    for mode in ["FLOOR", "CEILING", "KNEE", "BEST_NET", "LOW_COST"]:
        e = modes.get(mode)
        if not isinstance(e, dict):
            continue
        # pkl already has net_usd computed with original pip values
        # Recompute with correct pip value
        days = 1600  # approximate
        trigger = e.get("trigger", 0)
        trades = e.get("trades", 0)
        wr = e.get("wr", 0)
        pf = e.get("pf", 0)
        # Get pnl in pips from the pkl
        pnl_pips = e.get("pnl", 0)
        if pnl_pips is None:
            # Reconstruct from gross_usd
            gross_usd = e.get("gross_usd", 0)
            pnl_pips = gross_usd / pval if pval > 0 else 0

        spread = get_spread(csym)
        gross = pnl_pips * pval
        sprd_cost = trades * spread * pval
        comm_cost = trades * COMM
        net = gross - sprd_cost - comm_cost
        cost_pct = (sprd_cost + comm_cost) / gross * 100 if gross > 0 else 999
        tr_per_day = trades / days
        net_per_day = net / days

        std = {
            "trades": trades, "wr": wr, "pf": pf,
            "net_usd": net, "gross_usd": gross, "cost_pct": cost_pct,
            "tr_per_day": tr_per_day, "net_per_day": net_per_day,
            "mode": mode, "type": "FOREX", "days": days,
            "trigger": trigger, "multiplier": 0,
            "annualized": net_per_day * 365,
        }

        if best is None or net_per_day > best["net_per_day"]:
            best = std

    if best and best["net_per_day"] > 0:
        all_assets[csym] = best

# ── PROCESS CRYPTO (from JSON — keep best across ALL sections) ───────────
for sym, entries in [(s, e) for section in crypto_json.values() if isinstance(section, dict) for s, e in section.items()]:
    csym = sym.replace(".PRO", "").replace("_PRO", "")
    if not isinstance(entries, list):
        continue
    pval = pip_val(csym)
    days = entries[0].get("days", 1600) if entries else 1600

    best = None
    for e in entries:
        mode = "FLOOR" if e == entries[0] and len(entries) == 1 else "CEILING"
        std = make_std(e, csym, days, mode, "CRYPTO")
        if best is None or std["net_per_day"] > best["net_per_day"]:
            best = std
            best["mode"] = mode

    if best and best["net_per_day"] > 0:
        if csym not in all_assets or best["net_per_day"] > all_assets[csym]["net_per_day"]:
            all_assets[csym] = best

# ── PROCESS METALS/INDICES (from JSON — keep best per asset) ─────────────
for asset_key, data in mi_json.items():
    entries = data.get("floor", [])
    if not entries:
        continue
    days = entries[0].get("days", 1600)
    atype = "METAL" if asset_key in ("XAUUSD", "XAGUSD") else "INDEX"

    best = None
    for e in entries:
        std = make_std(e, asset_key, days, "FLOOR", atype)
        if best is None or std["net_per_day"] > best["net_per_day"]:
            best = std
            best["mode"] = "FLOOR"

    if best and best["net_per_day"] > 0:
        if asset_key not in all_assets or best["net_per_day"] > all_assets[asset_key]["net_per_day"]:
            all_assets[asset_key] = best

# ── VELOCITY RANKINGS ────────────────────────────────────────────────────
print("=" * 130)
print("CEREBUS VELOCITY OPTIMIZER v1.1 — FIXED")
print("=" * 130)
print(f"\nTotal assets with positive velocity: {len(all_assets)}")

ranked = sorted(all_assets.items(), key=lambda x: x[1]["net_per_day"], reverse=True)

print(f"\n{'='*130}")
print("VELOCITY RANKINGS — All Positive-Velocity Assets by Net/Day")
print("=" * 130)
print(f"\n  {'#':>3} {'Pair':10s} {'Type':8s} {'Mode':10s} {'Tr/d':>6s} {'Net/day':>10s} {'Annual$':>12s} {'Net total':>12s} {'WR%':>6s} {'PF':>6s} {'Cost%':>6s}")
print("  " + "-" * 105)
for i, (csym, d) in enumerate(ranked, 1):
    print(f"  {i:>3} {csym:10s} {d['type']:8s} {d['mode']:10s} {d['tr_per_day']:>6.2f} ${d['net_per_day']:>9.2f} ${d['annualized']:>11.0f} ${d['net_usd']:>11.0f} {d['wr']:>6.1f} {d['pf']:>6.1f} {d['cost_pct']:>6.1f}")

# ── MULTI-ASSET COMBOS ───────────────────────────────────────────────────
print(f"\n{'='*130}")
print("MULTI-ASSET VELOCITY COMBOS")
print("=" * 130)

GROUP_NAMES = {2:"DUOS",3:"TRIOS",4:"QUADS",5:"QUINTS",6:"HEX",7:"SEPTS",8:"OCTS",9:"NONS",10:"DECS"}

def basket_stats(combo):
    total_net = sum(d["net_usd"] for _, d in combo)
    total_trades = sum(d["trades"] for _, d in combo)
    avg_wr = sum(d["wr"] for _, d in combo) / len(combo)
    avg_pf = sum(d["pf"] for _, d in combo) / len(combo)
    max_days = max(d["days"] for _, d in combo)
    net_per_day = total_net / max_days
    tr_per_day = total_trades / max_days
    ann = net_per_day * 365
    types = defaultdict(int)
    for _, d in combo: types[d.get("type","?")] += 1
    return {"net_usd": total_net, "avg_wr": avg_wr, "avg_pf": avg_pf,
            "net_per_day": net_per_day, "annualized": ann, "tr_per_day": tr_per_day,
            "types": dict(types)}

def greedy_combos(pairs_list, size, key_fn, reverse=True, top_n=3):
    slist = sorted(pairs_list, key=key_fn, reverse=reverse)
    results = []; used_sets = set()
    for seed_idx in range(min(20, len(slist))):
        combo = [slist[seed_idx]]; used = {slist[seed_idx][0]}
        for _ in range(size - 1):
            best_next, best_score = None, (-9999999 if reverse else 9999999)
            for p in slist:
                if p[0] in used: continue
                score = key_fn(p)
                if (reverse and score > best_score) or (not reverse and score < best_score):
                    best_score = score; best_next = p
            if best_next: combo.append(best_next); used.add(best_next[0])
        if len(combo) == size:
            key = frozenset(c[0] for c in combo)
            if key not in used_sets: used_sets.add(key); results.append(combo)
        if len(results) >= top_n: break
    return results

pair_list = list(all_assets.items())

for size in range(2, min(15, len(pair_list)+1)):
    gname = GROUP_NAMES.get(size, f"{size}-SETS")
    print(f"\n  [{gname} — {size} assets]")

    for cat_name, key_fn in [
        ("MAX VELOCITY (net/day)", lambda p: p[1]["net_per_day"]),
        ("MAX NET TOTAL", lambda p: p[1]["net_usd"]),
        ("MAX FREQUENCY (tr/day)", lambda p: p[1]["tr_per_day"]),
    ]:
        combos = greedy_combos(pair_list, size, key_fn, reverse=True)
        if not combos:
            print(f"    [{cat_name}] (no combos)")
            continue
        m = basket_stats(combos[0])
        pairs_str = " + ".join(f"{c[0]}({c[1]['mode']})" for c in combos[0])
        print(f"    [{cat_name}]")
        print(f"      ${m['net_per_day']:.2f}/day | ${m['annualized']:.0f}/yr | {m['tr_per_day']:.1f} tr/d | {m['avg_wr']:.1f}% WR | PF {m['avg_pf']:.1f}")
        print(f"      {pairs_str}")

# ── SUMMARY ──────────────────────────────────────────────────────────────
print(f"\n{'='*130}")
print("OPTIMIZATION COMPLETE")
print("=" * 130)
