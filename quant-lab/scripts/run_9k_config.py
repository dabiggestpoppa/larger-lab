#!/usr/bin/env python3
"""
Run the 9K unlock config on ALL assets.
Uses per-asset trigger coefficients — NOT universal pip values.

The 9K config (C+D combined test, June 4):
1. ar_max=999 (no AR gate)
2. Trigger = native_trigger * coefficient (per-asset)
3. 4PM cutoff, flat DZ 20-50% (already in engine)
"""
import sys, json, time
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

TRIGGER_COEFFICIENTS = {
    "EURUSD": 0.83, "EURGBP": 0.65, "EURCHF": 0.65, "EURCAD": 0.65,
    "EURNZD": 0.55, "EURAUD": 0.55, "EURJPY": 0.55,
    "GBPUSD": 0.75, "GBPAUD": 0.75, "GBPCAD": 0.75, "GBPCHF": 0.75, "GBPJPY": 0.75, "GBPNZD": 0.75,
    "AUDUSD": 0.75, "AUDCAD": 0.65, "AUDCHF": 0.65, "AUDNZD": 0.65, "AUDJPY": 0.65,
    "NZDUSD": 0.75, "NZDCAD": 0.65, "NZDCHF": 0.65, "NZDJPY": 0.65,
    "USDCAD": 0.75, "USDCHF": 0.75, "USDJPY": 0.75,
    "CADCHF": 0.65, "CHFJPY": 0.75, "CADJPY": 0.65,
    "BTCUSD": 0.75, "ETHUSD": 0.75, "XAUUSD": 0.75, "XAGUSD": 0.75,
    "DE30": 0.75, "FR40": 0.75, "HK50": 0.75, "US500": 0.75,
}

ALL_PAIRS = [
    "EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD",
    "GBPUSD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD",
    "AUDUSD", "AUDCAD", "AUDCHF", "AUDNZD", "AUDJPY",
    "NZDUSD", "NZDCAD", "NZDCHF", "NZDJPY",
    "USDCAD", "USDCHF", "USDJPY", "CADCHF", "CHFJPY", "CADJPY",
    "BTCUSD", "ETHUSD", "XAUUSD", "XAGUSD", "DE30", "FR40", "HK50", "US500",
]

DATA_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data")
PIP_VALUES = {"BTCUSD": 1.0, "ETHUSD": 1.0, "XAUUSD": 0.10, "XAGUSD": 0.10,
               "US500": 1.0, "DE30": 1.0, "FR40": 1.0, "HK50": 1.0}

def get_pip_val(pair):
    return PIP_VALUES.get(pair, 0.07 if "JPY" in pair else 0.10)

def find_csv(pair):
    for p in [f"{pair}_PRO_M5.csv", f"{pair}_M5.csv", f"{pair}.csv"]:
        path = DATA_DIR / p
        if path.exists(): return path
    m = sorted(DATA_DIR.glob(f"{pair}*.csv"))
    return m[0] if m else None

def build_9k_config(pair):
    base = ASSET_CONFIGS[pair].copy()
    coeff = TRIGGER_COEFFICIENTS.get(pair, 0.75)
    tiers = {}
    for tn in ["T1", "T2", "T3"]:
        t = base["tiers"][tn]
        nt = t["trigger"]
        new_trig = round(nt * coeff, 1)
        ratio = t["au"] / nt if nt > 0 else 0.8
        tiers[tn] = {"ar_max": 999.0, "au": round(new_trig * ratio, 1), "trigger": new_trig}
    base["tiers"] = tiers
    return base

def run_pair(pair):
    csv_path = find_csv(pair)
    if not csv_path: return None
    config = build_9k_config(pair)
    pip = get_pip_val(pair)
    try:
        bars, _ = load_m5_csv(str(csv_path), pip_size=pip)
        if not bars: return None
        bt = SymmetryTrapBacktest(pip_size=pip, symbol=pair, config=config)
        r = bt.run(bars)
        nd = (bars[-1].timestamp.date() - bars[0].timestamp.date()).days
        tpd = r.total_trades / nd if nd > 0 else 0
        pf = r.profit_factor if r.profit_factor != float("inf") else 999.99
        return {"pair": pair, "trades": r.total_trades, "wr": round(r.win_rate, 2),
                "pf": round(pf, 2), "pnl_pips": round(r.total_pnl_pips, 1),
                "avg_win": round(r.avg_win_pips, 2), "avg_loss": round(r.avg_loss_pips, 2),
                "tr_per_day": round(tpd, 2), "n_days": nd, "tiers": config["tiers"]}
    except Exception as e:
        print(f"  ERROR {pair}: {e}")
        return None

def main():
    print("=" * 100)
    print("9K UNLOCK CONFIG — All assets, per-asset trigger coefficients")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 100)
    results = {}
    for pair in ALL_PAIRS:
        if pair not in ASSET_CONFIGS: continue
        print(f"{pair}...", end=" ", flush=True)
        t0 = time.time()
        r = run_pair(pair)
        e = time.time() - t0
        if r:
            results[pair] = r
            print(f"✓ {r['trades']} tr, WR={r['wr']:.1f}%, PF={r['pf']:.1f}, T/D={r['tr_per_day']:.2f}, T1={r['tiers']['T1']['trigger']}p ({e:.1f}s)")
        else:
            print(f"✗ ({e:.1f}s)")
    
    out = {"timestamp": datetime.now().isoformat(), "config": "9K_unlock", "results": results}
    with open(REPORTS_DIR / "run_9k_config_results.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    sr = sorted(results.values(), key=lambda x: x["trades"], reverse=True)
    print(f"\n{'Pair':12s} {'Trades':>7s} {'WR%':>6s} {'PF':>6s} {'Tr/D':>6s} {'T1_trig':>8s}")
    print("-" * 55)
    for r in sr:
        print(f"{r['pair']:12s} {r['trades']:>7d} {r['wr']:>6.1f} {r['pf']:>6.1f} {r['tr_per_day']:>6.2f} {r['tiers']['T1']['trigger']:>8.1f}")
    tt = sum(r["trades"] for r in results.values())
    aw = sum(r["wr"] for r in results.values()) / len(results) if results else 0
    print(f"\n{len(results)} pairs, {tt:,} total trades, avg WR: {aw:.1f}%")

if __name__ == "__main__":
    main()
