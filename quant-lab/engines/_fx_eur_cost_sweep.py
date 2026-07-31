"""
FX-EUR Basket Backtest — Trading Costs Sweep (Floor + Ceiling)
Optimized version with progress flushing.
"""

import sys
import os
import json
import copy

# Force unbuffered stdout
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)

QUANTLAB_ROOT = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab'
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest
from trading_costs import get_costs
from asset_configs import get_config

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')
REPORTS_DIR = os.path.join(QUANTLAB_ROOT, 'reports')

PAIRS = ['EURUSD', 'EURGBP', 'EURJPY', 'EURAUD', 'EURCAD', 'EURNZD', 'EURCHF']

CSV_MAP = {
    'EURUSD': 'EURUSD_M5.csv',
    'EURGBP': 'EURGBP_PRO_M5.csv',
    'EURJPY': 'EURJPY_PRO_M5.csv',
    'EURAUD': 'EURAUD_PRO_M5.csv',
    'EURCAD': 'EURCAD_PRO_M5.csv',
    'EURNZD': 'EURNZD_PRO_M5.csv',
    'EURCHF': 'EURCHF_PRO_M5.csv',
}


def find_csv(pair):
    fname = CSV_MAP.get(pair)
    if fname:
        fpath = os.path.join(DATA_DIR, fname)
        if os.path.exists(fpath):
            return fpath
    return None


def load_bars(pair):
    """Load CSV bars once, reuse for all sweeps."""
    from symmetry_trap_backtest import load_m5_csv
    csv_path = find_csv(pair)
    if not csv_path:
        return None, None
    costs = get_costs(pair)
    bars, symbol = load_m5_csv(csv_path, costs['pip_size'])
    print(f"  Loaded {len(bars)} bars for {pair}", flush=True)
    return bars, costs


def run_with_tiers(pair, bars, costs, tier_config, label=""):
    """Run backtest with given tier config on pre-loaded bars."""
    bt = SymmetryTrapBacktest(
        pip_size=costs['pip_size'],
        tier_config=tier_config,
        symbol=pair,
        config={'pip_value': costs['pip_size'], 'tiers': tier_config, 'name': pair},
        spread_pips=costs['spread_pips'],
        commission_pips=costs['commission_pips'],
    )
    result = bt.run(bars)
    print(f"  [{label}] WR={result.net_win_rate:.1f}% PF={result.net_profit_factor:.2f} "
          f"trades={result.total_trades} tr/day={result.total_trades/max(result.data_days,1):.2f} "
          f"net_PnL={result.net_pnl_pips:+.1f}p", flush=True)
    return result


def run_floor(pair, bars, costs):
    cfg = get_config(pair)
    return run_with_tiers(pair, bars, costs, cfg['tiers'], label="FLOOR")


def run_ceiling(pair, bars, costs):
    """Increase T1 trigger by 20% steps until WR < 81% or PF < 10."""
    cfg = get_config(pair)
    best_result = None

    for step in range(25):
        tier_config = copy.deepcopy(cfg['tiers'])
        mult = 1.0 + 0.20 * step
        tier_config['T1']['trigger'] = round(cfg['tiers']['T1']['trigger'] * mult, 2)

        result = run_with_tiers(pair, bars, costs, tier_config, 
                                label=f"CEIL step{step} mult={mult:.2f}x")

        net_wr = result.net_win_rate
        net_pf = result.net_profit_factor

        if net_wr < 81.0 or net_pf < 10.0:
            if best_result is not None:
                print(f"  [CEILING] Threshold crossed at mult={mult:.2f}x, "
                      f"returning previous step", flush=True)
                return best_result
            else:
                print(f"  [CEILING] Native already below threshold, returning native", flush=True)
                return result

        best_result = result

    print(f"  [CEILING] Max steps reached, returning highest mult result", flush=True)
    return best_result


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    results = {}

    for pair in PAIRS:
        print(f"\n{'='*60}", flush=True)
        print(f"PAIR: {pair}", flush=True)
        print(f"{'='*60}", flush=True)

        bars, costs = load_bars(pair)
        if bars is None:
            print(f"  [ERROR] No CSV found for {pair}", flush=True)
            continue

        # Floor
        print(f"  Running FLOOR (native triggers)...", flush=True)
        floor_result = run_floor(pair, bars, costs)

        # Ceiling
        print(f"  Running CEILING sweep...", flush=True)
        ceiling_result = run_ceiling(pair, bars, costs)

        results[pair] = {
            'floor': {
                'net_wr': round(floor_result.net_win_rate, 1),
                'net_pf': round(floor_result.net_profit_factor, 2),
                'net_trades': floor_result.total_trades,
                'net_pnl_pips': round(floor_result.net_pnl_pips, 1),
                'net_tr_per_day': round(floor_result.total_trades / max(floor_result.data_days, 1), 2),
                'data_days': floor_result.data_days,
            },
            'ceiling': {
                'net_wr': round(ceiling_result.net_win_rate, 1),
                'net_pf': round(ceiling_result.net_profit_factor, 2),
                'net_trades': ceiling_result.total_trades,
                'net_pnl_pips': round(ceiling_result.net_pnl_pips, 1),
                'net_tr_per_day': round(ceiling_result.total_trades / max(ceiling_result.data_days, 1), 2),
                'data_days': ceiling_result.data_days,
            },
        }

    # Save JSON
    out_path = os.path.join(REPORTS_DIR, 'fx_eur_cost_sweep.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n\nResults saved to {out_path}", flush=True)

    # Print summary table
    print(f"\n{''*10}> FX-EUR BASKET COST SWEEP SUMMARY", flush=True)
    header = f"  {'Pair':<10} | {'Floor WR%':>9} | {'Floor PF':>8} | {'Floor t/d':>9} | {'Ceil WR%':>9} | {'Ceil PF':>8} | {'Ceil t/d':>9}"
    print(header, flush=True)
    print(f"  {'-'*10}-+-{'-'*9}-+-{'-'*8}-+-{'-'*9}-+-{'-'*9}-+-{'-'*8}-+-{'-'*9}", flush=True)
    for pair in PAIRS:
        if pair in results:
            r = results[pair]
            print(f"  {pair:<10} | {r['floor']['net_wr']:>8.1f}% | {r['floor']['net_pf']:>7.2f} | "
                  f"{r['floor']['net_tr_per_day']:>8.2f} | "
                  f"{r['ceiling']['net_wr']:>8.1f}% | {r['ceiling']['net_pf']:>7.2f} | "
                  f"{r['ceiling']['net_tr_per_day']:>8.2f}", flush=True)

    return results


if __name__ == '__main__':
    main()
