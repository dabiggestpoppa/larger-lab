"""
Uniform FLOOR/KNEE/CEILING report v2 -- FIXED PIP VALUES.
MAD directive: ALL assets use pip_value = $0.10 minimum.
Metals are futures contracts, not CFDs -- same pip treatment as FX.
Crypto pip_value = $1.0 (confirmed).
Indices pip_value = $1.0 (confirmed).
"""
import sys, json, os, pickle
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
COMM = 0.07

# FIXED: All assets use $0.10 pip value minimum (futures convention)
# Crypto: $1.0 (correct), Indices: $1.0 (correct), Metals: $0.10 (was incorrectly $0.01 for XAG)
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
    if pair in ("BTCUSD", "ETHUSD"): return 1.0
    if pair in ("XAUUSD", "XAGUSD"): return 0.10  # FIXED: metals = futures, min pip $0.10
    if pair in ("US500", "DE30", "FR40", "HK50"): return 1.0
    if "JPY" in pair: return 0.07  # JPY pairs are the only exception
    return 0.10

def calc_net(entry, pair):
    trades = entry.get("trades", 0)
    wr = entry.get("wr", 0)
    pf = entry.get("pf", 0)
    pnl = entry.get("pnl", 0)
    tr_d = entry.get("tr_per_day", 0)
    trigger = entry.get("t1_trigger", 0)
    mult = entry.get("multiplier", 0)
    pval = get_pip_val(pair)
    spread = get_spread(pair)
    gross = pnl * pval
    sprd_cost = trades * spread * pval
    comm_cost = trades * COMM
    net = gross - sprd_cost - comm_cost
    cost_pct = (sprd_cost + comm_cost) / gross * 100 if gross > 0 else 999
    return {
        "trigger": trigger, "multiplier": mult, "trades": trades, "wr": wr, "pf": pf,
        "tr_per_day": tr_d, "gross_usd": gross, "sprd_usd": sprd_cost,
        "comm_usd": comm_cost, "net_usd": net, "cost_pct": cost_pct,
        "spread": spread, "pnl": pnl,
    }

# Load data
with open(os.path.join(REPORTS_DIR, "trigger_sweep_metals_indices.json")) as f:
    mi_data = json.load(f)

# UNIFORM TABLE
print("=" * 130)
print("UNIFORM SWEEP RESULTS -- METALS & INDICES (v2 -- CORRECTED PIP VALUES)")
print("=" * 130)

for asset_key in ["XAUUSD", "XAGUSD", "US500", "DE30", "FR40", "HK50"]:
    entries = mi_data.get(asset_key, {}).get("floor", [])
    if not entries:
        print(f"\n{asset_key}: NO DATA")
        continue

    pval = get_pip_val(asset_key)
    spread = get_spread(asset_key)

    # Operating points — EACH MUST BE A DISTINCT ENTRY
    # FLOOR = max trades
    floor_e = max(entries, key=lambda e: e.get("trades", 0))
    # CEILING = max WR (min 100 trades to avoid tiny-sample artifacts)
    valid_ceil = [e for e in entries if e.get("trades", 0) >= 100]
    ceil_e = max(valid_ceil, key=lambda e: e.get("wr", 0)) if valid_ceil else max(entries, key=lambda e: e.get("wr", 0))
    # KNEE = best PF (WR>=80%, min 100 trades), but NOT the same as CEILING
    valid_knee = [e for e in entries if e.get("wr", 0) >= 80 and e.get("trades", 0) >= 100 and e is not ceil_e]
    if not valid_knee:
        valid_knee = [e for e in entries if e.get("wr", 0) >= 80 and e.get("trades", 0) >= 100]
    knee_e = max(valid_knee, key=lambda e: e.get("pf", 0)) if valid_knee else max(entries, key=lambda e: e.get("pf", 0))
    # BEST_NET = highest net USD, but NOT same as FLOOR or CEILING or KNEE
    net_entries = [(e, calc_net(e, asset_key)) for e in entries if e is not floor_e and e is not ceil_e and e is not knee_e]
    if not net_entries:
        net_entries = [(e, calc_net(e, asset_key)) for e in entries]
    best_net_e, _ = max(net_entries, key=lambda x: x[1]["net_usd"])

    print(f"\n  {asset_key}  |  pip_value=${pval}  |  spread={spread}p  |  {entries[0]['days']} days")
    print("  " + "-" * 115)
    print(f"  {'Mode':10s} {'Mult':>6s} {'Trigger':>8s} {'Trades':>7s} {'WR%':>6s} {'PF':>7s} {'Tr/d':>6s} {'Net$':>12s} {'Cost%':>7s} {'Pnl':>10s}")
    print("  " + "-" * 115)

    for label, e in [("FLOOR", floor_e), ("KNEE", knee_e), ("CEILING", ceil_e), ("BEST_NET", best_net_e)]:
        c = calc_net(e, asset_key)
        print(f"  {label:10s} {e['multiplier']:>6.1f} {e['t1_trigger']:>8.1f} {e['trades']:>7d} {e['wr']:>6.1f} {e['pf']:>7.1f} {e['tr_per_day']:>6.2f} ${c['net_usd']:>10.2f} {c['cost_pct']:>7.1f} {e['pnl']:>10.1f}")

print("\n\n" + "=" * 130)
print("CORRECTED PIP VALUE TABLE -- ALL ASSET CLASSES")
print("=" * 130)
print(f"""
  Asset Class  |  Pip Value  |  Notes
  {'-'*60}
  FX Majors    |  $0.10     |  Standard (EURUSD, GBPUSD, etc.)
  FX JPY Cross |  $0.07     |  JPY-denominated exception
  Crypto       |  $1.00     |  BTCUSD, ETHUSD
  Metals       |  $0.10     |  Futures contracts (XAU, XAG) -- NOT CFD
  Indices      |  $1.00     |  US500, DE30, FR40, HK50
""")

print("=" * 130)
print("END")
print("=" * 130)
