#!/usr/bin/env python3
"""
FINAL COMBINATORICS — Updated with:
1. No commission on indices
2. JPY pairs use historical spread from 2023 onward
3. Flat $0.07 commission for FX/crypto/metals
4. Updated spread values from CSV data
"""
import json
import pickle
import os
from itertools import combinations
from pathlib import Path

REPORTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")

# ── Commission ───────────────────────────────────────────────────────────
# Flat $0.07 per trade at 0.01 lot for FX/crypto/metals
# NO commission on indices (MAD directive)
COMM_USD = 0.07

def comm_pips(pair):
    """Convert $0.07 to pips. Indices = $0 commission."""
    if pair in ('DE30', 'FR40', 'HK50', 'US500', 'NAS100'):
        return 0.0  # No commission on indices
    if 'JPY' in pair:
        return 0.07 / 1000.0
    if pair in ('BTCUSD', 'ETHUSD', 'XAUUSD', 'XAGUSD'):
        return 0.07 / 1.0
    return 0.07 / 10.0

# ── Spreads (pips) — MT5 live values (current trading conditions) ──────
# JPY pairs: MT5 spread (CSV spread column unreliable — values too high)
# Non-JPY crosses: MT5 spread (CSV PRO files had unit conversion issues)
# Majors: MT5 spread (non-PRO files have no spread column)
SPREADS = {
    # FX majors
    "EURUSD": 0.1, "GBPUSD": 0.3, "USDJPY": 0.3,
    "USDCHF": 0.3, "AUDUSD": 0.3, "NZDUSD": 0.3, "USDCAD": 0.3,
    # FX crosses
    "EURGBP": 0.3, "EURJPY": 0.5, "GBPJPY": 0.5,
    "EURCHF": 0.3, "AUDJPY": 0.5, "NZDJPY": 0.5, "AUDNZD": 0.5,
    "AUDCAD": 0.5, "AUDCHF": 0.5, "CADJPY": 0.5, "CHFJPY": 0.5,
    "CADCHF": 0.5, "EURNZD": 0.7, "EURAUD": 0.5, "EURCAD": 0.5,
    "GBPAUD": 0.5, "GBPCAD": 0.5, "GBPCHF": 0.5, "GBPNZD": 0.7,
    "NZDCAD": 0.5, "NZDCHF": 0.7,
    # Crypto
    "BTCUSD": 5.0, "ETHUSD": 5.0,
    # Metals
    "XAUUSD": 1.5, "XAGUSD": 1.5,
    # Indices
    "DE30": 0.5, "FR40": 0.5, "HK50": 0.5, "US500": 0.5,
}

def get_spread(pair):
    return SPREADS.get(pair, 0.5)

def get_pip_val(pair):
    """Pip value in USD per pip at 0.01 lot size."""
    if pair in ("BTCUSD", "ETHUSD"):
        return 0.01  # $1/pip at 1.0 lot → $0.01 at 0.01 lot
    if pair in ("XAUUSD", "XAGUSD"):
        return 0.01  # $1/pip at 1.0 lot → $0.01 at 0.01 lot
    if pair in ("DE30", "FR40", "HK50", "US500", "NAS100"):
        return 0.01  # $1/pip at 1.0 lot → $0.01 at 0.01 lot
    # All FX: 1 pip = $10 at 1.0 lot → $0.10 at 0.01 lot
    return 0.10

def calc_net(entry, pair):
    """Convert raw sweep entry to net USD."""
    trades = entry.get("trades", 0)
    wr = entry.get("wr", 0)
    pf = entry.get("pf", 0)
    pnl = entry.get("pnl", 0)
    tr_d = entry.get("tr_per_day", 0)
    pval = get_pip_val(pair)
    spread = get_spread(pair)
    comm = comm_pips(pair)
    
    gross = pnl * pval
    sprd_cost = trades * spread * pval
    comm_cost = trades * comm * pval  # comm in pips * pip_value = USD
    # Actually comm is already in pips, so comm_cost = trades * comm_pips * pip_value
    # But comm_pips = $0.07 / pip_value, so comm_cost = trades * $0.07
    # Simpler: comm_cost = trades * 0.07 (flat dollar amount)
    comm_cost = trades * COMM_USD if pair not in ('DE30','FR40','HK50','US500','NAS100') else 0.0
    net = gross - sprd_cost - comm_cost
    cost_pct = (sprd_cost + comm_cost) / gross * 100 if gross > 0 else 999
    
    return {
        "trades": trades, "wr": wr, "pf": pf, "tr_per_day": tr_d,
        "gross_usd": gross, "sprd_usd": sprd_cost, "comm_usd": comm_cost,
        "net_usd": net, "cost_pct": cost_pct, "spread": spread,
    }

# ── Load data ────────────────────────────────────────────────────────────
print("Loading data...")
with open(REPORTS_DIR / "_matrix_data.pkl", "rb") as f:
    forex_data = pickle.load(f)

with open(REPORTS_DIR / "trigger_sweep_crypto.json") as f:
    crypto_raw = json.load(f)

with open(REPORTS_DIR / "trigger_sweep_metals_indices.json") as f:
    metals_raw = json.load(f)

# ── Build all pairs ─────────────────────────────────────────────────────
all_pairs = {}

# Forex — use FLOOR mode (max trades, our operating point)
# Pickle has pre-calculated gross_usd (using $0.10/pip for all FX).
# We just need to adjust spread and commission costs.
for sym, data in forex_data.items():
    e = data.get("FLOOR")
    if e and isinstance(e, dict):
        trades = e.get("trades", 0)
        wr = e.get("wr", 0)
        pf = e.get("pf", 0)
        tr_d = e.get("tr_per_day", 0)
        gross = e.get("gross_usd", 0)  # Already in USD from pickle
        
        # Recalculate spread cost with OUR spread value
        spread = get_spread(sym)
        pval = get_pip_val(sym)
        sprd_cost = trades * spread * pval
        
        # Commission: flat $0.07 per trade (no commission on indices)
        comm_cost = trades * COMM_USD
        
        net = gross - sprd_cost - comm_cost
        cost_pct = (sprd_cost + comm_cost) / gross * 100 if gross > 0 else 999
        
        ne = {
            "trades": trades, "wr": wr, "pf": pf, "tr_per_day": tr_d,
            "gross_usd": gross, "sprd_usd": sprd_cost, "comm_usd": comm_cost,
            "net_usd": net, "cost_pct": cost_pct, "spread": spread,
            "mode": "FLOOR", "type": "FOREX",
        }
        all_pairs[sym] = ne

# Crypto
for section, pairs_data in crypto_raw.items():
    mode_name = "FLOOR" if section == "floor" else "CEILING"
    if not isinstance(pairs_data, dict):
        continue
    for sym, entries in pairs_data.items():
        csym = sym.replace(".PRO", "").replace("_PRO", "")
        if not isinstance(entries, list):
            continue
        best_e, best_net = None, -999999
        for e in entries:
            ne = calc_net(e, csym)
            ne["mode"] = mode_name
            ne["type"] = "CRYPTO"
            if ne["net_usd"] > best_net:
                best_net = ne["net_usd"]
                best_e = ne
        if best_e and (csym not in all_pairs or best_e["net_usd"] > all_pairs[csym].get("net_usd", -999999)):
            all_pairs[csym] = best_e

# Metals/Indices
for asset, data in metals_raw.items():
    floor_entries = data.get("floor", [])
    if not floor_entries:
        continue
    floor_e = max(floor_entries, key=lambda e: e.get("trades", 0))
    floor_c = calc_net(floor_e, asset)
    floor_c["mode"] = "FLOOR"
    floor_c["type"] = "METAL" if asset in ("XAUUSD", "XAGUSD") else "INDEX"
    if asset not in all_pairs or floor_c["net_usd"] > all_pairs[asset].get("net_usd", -999999):
        all_pairs[asset] = floor_c

print(f"Total pairs: {len(all_pairs)}")

# ── Rankings ─────────────────────────────────────────────────────────────
sorted_all = sorted(all_pairs.items(), key=lambda x: x[1]["net_usd"], reverse=True)

print("\n" + "=" * 110)
print("ALL PAIRS RANKED BY NET PROFIT (best config per pair)")
print("=" * 110)
print(f"{'#':>3s} {'Pair':10s} {'Type':8s} {'Mode':10s} {'Trades':>7s} {'WR%':>6s} {'PF':>6s} {'Tr/d':>6s} {'Net$':>12s} {'Cost%':>6s}")
print("-" * 110)
for i, (sym, e) in enumerate(sorted_all, 1):
    print(f"{i:3d} {sym:10s} {e.get('type',''):8s} {e.get('mode',''):10s} {e['trades']:>7d} {e['wr']:>6.1f} "
          f"{e['pf']:>6.1f} {e.get('tr_per_day',0):>6.2f} ${e['net_usd']:>10.2f} {e['cost_pct']:>6.1f}")

# ── Categories ───────────────────────────────────────────────────────────
categories = {
    "MAX PROFIT (net > $3,000)": [],
    "LOW COST (cost% < 10%)": [],
    "HIGH ACCURACY (WR > 85%)": [],
    "HIGH FREQUENCY (tr/d > 1.0)": [],
    "AVOID (cost% > 25%)": [],
}

for sym, e in sorted_all:
    if e["net_usd"] > 3000:
        categories["MAX PROFIT (net > $3,000)"].append((sym, e))
    if e["cost_pct"] < 10:
        categories["LOW COST (cost% < 10%)"].append((sym, e))
    if e["wr"] > 85:
        categories["HIGH ACCURACY (WR > 85%)"].append((sym, e))
    if e.get("tr_per_day", 0) > 1.0:
        categories["HIGH FREQUENCY (tr/d > 1.0)"].append((sym, e))
    if e["cost_pct"] > 25:
        categories["AVOID (cost% > 25%)"].append((sym, e))

print("\n" + "=" * 110)
print("CATEGORIES")
print("=" * 110)
for cat_name, items in categories.items():
    print(f"\n--- {cat_name} ({len(items)} pairs) ---")
    for sym, e in items:
        print(f"  {sym:10s} {e.get('type',''):8s} Net: ${e['net_usd']:>10.2f} | WR: {e['wr']:5.1f}% | PF: {e['pf']:5.1f} | Cost: {e['cost_pct']:5.1f}%")

# ── Optimal Baskets ──────────────────────────────────────────────────────
print("\n" + "=" * 110)
print("OPTIMAL BASKETS (2-14 assets)")
print("=" * 110)

# Sort pairs by net_usd for basket building
viable = [(sym, e) for sym, e in sorted_all if e["net_usd"] > 0]
viable.sort(key=lambda x: x[1]["net_usd"], reverse=True)

print(f"{'Assets':>6s} {'Net$':>12s} {'Avg WR%':>8s} {'Trades':>8s} {'Pairs'}")
print("-" * 110)

for n in range(2, min(15, len(viable) + 1)):
    basket = viable[:n]
    total_net = sum(e["net_usd"] for _, e in basket)
    total_trades = sum(e["trades"] for _, e in basket)
    avg_wr = sum(e["wr"] for _, e in basket) / len(basket)
    pairs_str = ", ".join(s for s, _ in basket)
    print(f"{n:6d} ${total_net:>10.2f} {avg_wr:8.1f} {total_trades:8d} {pairs_str}")

# Save
output = {
    "pairs": {sym: e for sym, e in sorted_all},
    "categories": {k: [(s, e) for s, e in v] for k, v in categories.items()},
}
with open(REPORTS_DIR / "combinatorics_final.json", "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"\nSaved to: {REPORTS_DIR / 'combinatorics_final.json'}")
