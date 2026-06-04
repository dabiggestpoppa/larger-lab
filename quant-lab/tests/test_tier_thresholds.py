"""
ISOLATED HYPOTHESIS TEST: Tier Threshold Validity
===================================================
Tests whether K-Means calibrated tier thresholds produce sensible
trade counts relative to the Phase 0 baseline (EURUSD).

Hypothesis: EURGBP trigger (8p) < EURUSD trigger (12p) should produce
MORE trades, not fewer. If EURGBP produces fewer, the K-Means config is wrong.

Phase 0 engine is imported read-only. No engine modifications.
"""
import sys, os
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest

# Clean window: 2022-01-01 onwards (where all pairs have full 24h coverage)
CLEAN_START = "2022-01-01"

pairs_to_test = [
    ("EURUSD", r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'),
    ("EURGBP", r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURGBP_PRO_M5.csv'),
]

print("=" * 70)
print("ISOLATED TEST: Tier Threshold Validity")
print("Clean window: {} onwards".format(CLEAN_START))
print("=" * 70)

results = {}
for asset_key, csv_path in pairs_to_test:
    if asset_key not in ASSET_CONFIGS:
        print("SKIP {}: no config".format(asset_key))
        continue
    
    config = ASSET_CONFIGS[asset_key]
    print("\n--- {} ---".format(asset_key))
    print("Config: pip={}, T1(ar_max={}, trigger={}, au={})".format(
        config["pip_value"],
        config["tiers"]["T1"]["ar_max"],
        config["tiers"]["T1"]["trigger"],
        config["tiers"]["T1"]["au"],
    ))
    
    bt = SymmetryTrapBacktest(
        pip_size=config["pip_value"],
        tier_config=config["tiers"],
        symbol=asset_key,
        config=config,
    )
    result = bt.run_from_csv(csv_path)
    
    # Count trades by tier
    tier_counts = {}
    if result.trades:
        for t in result.trades:
            tier = getattr(t, 'tier', 'UNKNOWN')
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    trades_per_day = round(result.total_trades / result.data_days, 3) if result.data_days else 0
    
    print("Results: {} trades | {} days | {:.3f} tr/day | WR: {:.1f}%".format(
        result.total_trades, result.data_days, trades_per_day, result.win_rate))
    print("Tier distribution: {}".format(tier_counts))
    print("Loop stats: {}".format(result.loop_stats))
    
    results[asset_key] = {
        'trades': result.total_trades,
        'days': result.data_days,
        'tr_per_day': trades_per_day,
        'wr': result.win_rate,
        'tier_counts': tier_counts,
        'config': config,
    }

# Comparison
if 'EURUSD' in results and 'EURGBP' in results:
    eurusd = results['EURUSD']
    eurgbp = results['EURGBP']
    
    print("\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print("EURUSD: trigger={}p | {} tr/day | {} total trades".format(
        eurusd['config']['tiers']['T1']['trigger'],
        eurusd['tr_per_day'], eurusd['trades']))
    print("EURGBP: trigger={}p | {} tr/day | {} total trades".format(
        eurgbp['config']['tiers']['T1']['trigger'],
        eurgbp['tr_per_day'], eurgbp['trades']))
    
    print("\nEURGBP trigger is {}p vs EURUSD {}p ({}% smaller)".format(
        eurgbp['config']['tiers']['T1']['trigger'],
        eurusd['config']['tiers']['T1']['trigger'],
        round((1 - eurgbp['config']['tiers']['T1']['trigger'] / eurusd['config']['tiers']['T1']['trigger']) * 100, 1)
    ))
    
    if eurgbp['tr_per_day'] < eurusd['tr_per_day']:
        print(">>> HYPOTHESIS FALSIFIED: EURGBP has smaller trigger but fewer trades/day")
        print(">>> K-Means tier thresholds are WRONG for EURGBP")
    else:
        print(">>> HYPOTHESIS SUPPORTED: EURGBP has smaller trigger and more trades/day")
