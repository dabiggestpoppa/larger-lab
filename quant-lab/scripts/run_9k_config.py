#!/usr/bin/env python3
"""
Run the 9K unlock config on ALL assets.
This is the same config that produced 9,228 trades on EURUSD (C+D combined test).

Key: Each pair uses its OWN native trigger scaled by a coefficient.
NOT a universal 8-10p across all pairs.

The 9K config:
1. ar_max=999 (no AR gate / session filter only)
2. Trigger = native_trigger * coefficient (0.65x for most, 0.55x for high-trigger crosses)
3. Session cutoff: 4PM EST (ACTIVATION_END = time(16, 0))
4. Flat DZ: 20-50% for all loops (no dynamic DZ)
5. No 4h timeout, no 80% kill switch (already removed from engine)
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports")

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

# ═══════════════════════════════════════════════════════════
# 9K UNLOCK CONFIG — Per-asset trigger coefficients
# ═══════════════════════════════════════════════════════════
# The coefficient is applied to each pair's NATIVE trigger
# NOT a universal pip value

# Coefficient groups based on the frequency normalization sweep results:
# - 0.65x: Standard FX pairs (EURGBP, EURCHF, EURCAD, GBPUSD, etc.)
# - 0.55x: High-trigger crosses (EURJPY, EURAUD, EURNZD, etc.)
# - 0.75x: Already-high-frequency pairs (EURUSD, GBPJPY, USDJPY, CHFJPY)

TRIGGER_COEFFICIENTS = {
    # EUR Basket
    "EURUSD": 0.83,   # 12p → 10p (the calibrated value that gave 6,686 trades)
    "EURGBP": 0.65,   # 8p → 5.2p
    "EURCHF": 0.65,   # 11p → 7.2p
    "EURCAD": 0.65,   # 16p → 10.4p
    "EURNZD": 0.55,   # 34p → 18.7p
    "EURAUD": 0.55,   # 32p → 17.6p
    "EURJPY": 0.55,   # 35p → 19.2p
    # GBP Basket
    "GBPUSD": 0.75,   # 16p → 12p
    "GBPAUD": 0.75,   # 25p → 18.8p
    "GBPCAD": 0.75,   # 24p → 18p
    "GBPCHF": 0.75,   # 21p → 15.8p
    "GBPJPY": 0.75,   # 23p → 17.3p
    "GBPNZD": 0.75,   # 29p → 21.8p
    # AUD Basket
    "AUDUSD": 0.75,   # 13p → 9.8p
    "AUDCAD": 0.65,   # 16p → 10.4p
    "AUDCHF": 0.65,   # 12p → 7.8p
    "AUDNZD": 0.65,   # 14p → 9.1p
    "AUDJPY": 0.65,   # 26p → 16.9p
    # NZD Basket
    "NZDUSD": 0.75,   # 17p → 12.8p
    "NZDCAD": 0.65,   # 15p → 9.8p
    "NZDCHF": 0.65,   # 11p → 7.2p
    "NZDJPY": 0.65,   # 24p → 15.6p
    # USD/CHF/CAD
    "USDCAD": 0.75,   # 13p → 9.8p
    "USDCHF": 0.75,   # 11p → 8.3p
    "USDJPY": 0.75,   # 19p → 14.3p
    # CHF/JPY crosses
    "CADCHF": 0.65,   # 9p → 5.9p
    "CHFJPY": 0.75,   # 17p → 12.8p
    "CADJPY": 0.65,   # 23p → 15p
    # Crypto
    "BTCUSD": 0.75,   # 246p → 184.5p
    "ETHUSD": 0.75,   # 42p → 31.5p
    # Metals
    "XAUUSD": 0.75,   # 19p → 14.3p
    "XAGUSD": 0.75,   # 30p → 22.5p
    # Indices
    "DE30": 0.75,     # 27p → 20.3p
    "FR40": 0.75,     # 23p → 17.3p
    "HK50": 0.75,     # 110p → 82.5p
    "US500": 0.75,    # 23p → 17.3p
}

# All pairs to run
ALL_PAIRS = [
    "EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD",
    "GBPUSD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD",
    "AUDUSD", "AUDCAD", "AUDCHF", "AUDNZD", "AUDJPY",
    "NZDUSD", "NZDCAD", "NZDCHF", "NZDJPY",
    "USDCAD", "USDCHF", "USDJPY",
    "CADCHF", "CHFJPY", "CADJPY",
    "BTCUSD", "ETHUSD", "XAUUSD", "XAGUSD",
    "DE30", "FR40", "HK50", "US500",
]

DATA_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data")

def find_csv(pair):
    for pattern in [f"{pair}_PRO_M5.csv", f"{pair}_M5.csv", f"{pair}.csv"]:
        p = DATA_DIR / pattern
        if p.exists():
            return p
    matches = sorted(DATA_DIR.glob(f"{pair}*.csv"))
    return matches[0] if matches else None

def build_9k_config(pair):
    """Build the 9K unlock config for a specific pair."""
    base = ASSET_CONFIGS[pair]
    coeff = TRIGGER_COEFFICIENTS.get(pair, 0.75)
    
    tiers = {}
    for tier_name in ["T1", "T2", "T3"]:
        t = base["tiers"][tier_name]
        native_trigger = t["trigger"]
        # Scale trigger by coefficient, keep AU proportional
        new_trigger = round(native_trigger * coeff, 1)
        # AU should also scale proportionally
        au_ratio = t["au"] / native_trigger if native_trigger > 0 else 0.8
        new_au = round(new_trigger * au_ratio, 1)
        
        tiers[tier_name] = {
            "ar_max": 999.0,  # No AR gate
            "au": new_au,
            "trigger": new_trigger,
        }
    
    return tiers

def run_pair(pair):
    """Run backtest for a single pair with 9K config."""
    csv_path = find_csv(pair)
    if csv_path is None:
        print(f"  {pair}: NO CSV FILE")
        return None
    
    base_config = ASSET_CONFIGS[pair]
    tiers = build_9k_config(pair)
    
    pip_value = base_config.get("pip_value", 0.0001)
    
    try:
        bars, _ = load_m5_csv(str(csv_path), pip_size=pip_value)
        if not bars:
            print(f"  {pair}: NO BARS")
            return None
        
        bt = SymmetryTrapBacktest(
            pip_size=pip_value,
            tier_config=tiers,
            config=base_config,
            symbol=pair,
        )
        
        # Run the backtest
        bt.run(bars)
        results = bt.results()
        
        n_days = (bars[-1].timestamp.date() - bars[0].timestamp.date()).days
        tr_per_day = results["trades"] / n_days if n_days > 0 else 0
        
        return {
            "pair": pair,
            "trades": results["trades"],
            "wr": results["wr"],
            "pf": results["pf"],
            "pnl_pips": results["pnl_pips"],
            "avg_win": results.get("avg_win", 0),
            "avg_loss": results.get("avg_loss", 0),
            "tr_per_day": round(tr_per_day, 2),
            "n_days": n_days,
            "tiers": tiers,
            "csv_file": csv_path.name,
        }
    except Exception as e:
        print(f"  {pair}: ERROR - {e}")
        return None

def main():
    print("=" * 100)
    print("9K UNLOCK CONFIG — Running on ALL assets")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 100)
    print()
    
    all_results = {}
    
    for pair in ALL_PAIRS:
        if pair not in ASSET_CONFIGS:
            print(f"  {pair}: NOT IN ASSET_CONFIGS, skipping")
            continue
        
        print(f"Running {pair}...", end=" ")
        t0 = time.time()
        result = run_pair(pair)
        elapsed = time.time() - t0
        
        if result:
            all_results[pair] = result
            print(f"✓ {result['trades']} trades, WR={result['wr']:.1f}%, PF={result['pf']:.1f}, "
                  f"Tr/D={result['tr_per_day']:.2f}, T1_trigger={result['tiers']['T1']['trigger']}p ({elapsed:.1f}s)")
        else:
            print(f"✗ ({elapsed:.1f}s)")
    
    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "config": "9K_unlock",
        "description": "No AR gate (ar_max=999), per-asset trigger coefficient, 4PM cutoff, flat DZ 20-50%",
        "results": all_results,
    }
    
    output_path = REPORTS_DIR / "run_9k_config_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    # Print summary
    print()
    print("=" * 100)
    print("SUMMARY — 9K Config Results")
    print("=" * 100)
    
    sorted_results = sorted(all_results.values(), key=lambda x: x["trades"], reverse=True)
    
    print(f"\n{'Pair':12s} {'Trades':>7s} {'WR%':>6s} {'PF':>6s} {'Tr/D':>6s} {'T1_trig':>8s} {'AU':>6s}")
    print("-" * 60)
    for r in sorted_results:
        t1 = r["tiers"]["T1"]
        print(f"{r['pair']:12s} {r['trades']:>7d} {r['wr']:>6.1f} {r['pf']:>6.1f} {r['tr_per_day']:>6.2f} {t1['trigger']:>8.1f} {t1['au']:>6.1f}")
    
    total_trades = sum(r["trades"] for r in all_results.values())
    avg_wr = sum(r["wr"] for r in all_results.values()) / len(all_results) if all_results else 0
    print(f"\nTotal: {len(all_results)} pairs, {total_trades:,} trades, avg WR: {avg_wr:.1f}%")
    print(f"\nResults saved to: {output_path}")

if __name__ == "__main__":
    main()
