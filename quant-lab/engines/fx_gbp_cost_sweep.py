"""
FX-GBP Basket Cost Sweep — Floor (native) vs Ceiling (T1 trigger ↑ until WR < 81% or PF < 10)
=============================================================================================
AR expansion = 3.0x, session cutoff = 4PM EST (16:00).
Trading costs: spread + commission per trading_costs.py
"""

import sys
import os
import json
import copy

# Force unbuffered stdout for Windows
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

QUANTLAB_ROOT = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab'
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from trading_costs import get_costs
from asset_configs import get_config

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')
REPORTS_DIR = os.path.join(QUANTLAB_ROOT, 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)

PAIRS = ['GBPUSD', 'GBPJPY', 'GBPAUD', 'GBPCAD', 'GBPNZD', 'GBPCHF']

# Map pair → CSV file
CSV_MAP = {
    'GBPUSD': 'GBPUSD_M5.csv',
    'GBPJPY': 'GBPJPY_M5.csv',
    'GBPAUD': 'GBPAUD_M5.csv',
    'GBPCAD': 'GBPCAD_PRO_M5.csv',
    'GBPNZD': 'GBPNZD_M5.csv',
    'GBPCHF': 'GBPCHF_M5.csv',
}


def run_backtest(pair, cfg, costs, t1_trigger_override=None):
    """Run a single backtest. Optionally override T1 trigger."""
    csv_file = CSV_MAP[pair]
    csv_path = os.path.join(DATA_DIR, csv_file)
    if not os.path.exists(csv_path):
        print(f"  WARNING: CSV not found: {csv_path}")
        return None

    # Deep copy config so we can override T1 trigger
    cfg_copy = copy.deepcopy(cfg)
    if t1_trigger_override is not None:
        cfg_copy['tiers']['T1']['trigger'] = t1_trigger_override

    bt = SymmetryTrapBacktest(
        config=cfg_copy,
        spread_pips=costs['spread_pips'],
        commission_pips=costs['commission_pips'],
    )
    result = bt.run_from_csv(csv_path)
    return result


def trades_per_day(result):
    """Compute average net trades per day."""
    if result.data_days == 0:
        return 0.0
    return round(result.total_trades / result.data_days, 3)


def find_ceiling(pair, cfg, costs):
    """
    Increase T1 trigger by 20% steps until net WR < 81% OR net PF < 10.
    Returns (ceiling_trigger, result_at_ceiling).
    """
    native_t1 = cfg['tiers']['T1']['trigger']
    multiplier = 1.20
    step = 0

    while True:
        step += 1
        new_trigger = round(native_t1 * (multiplier ** step), 2)
        result = run_backtest(pair, cfg, costs, t1_trigger_override=new_trigger)
        if result is None or result.total_trades == 0:
            # If no trades, we've gone too far — return previous step
            # But for first step, return this one
            return new_trigger, result

        net_wr = result.net_win_rate
        net_pf = result.net_profit_factor

        print(f"    Ceiling step {step}: T1={new_trigger} -> WR={net_wr:.1f}%, PF={net_pf:.2f}, tr={result.total_trades}")

        if net_wr < 81.0 or net_pf < 10.0:
            return new_trigger, result

        # Safety: don't go beyond 5x native
        if new_trigger > native_t1 * 5.0:
            return new_trigger, result


def main():
    all_results = {}

    for pair in PAIRS:
        print(f"\n{'='*60}")
        print(f"  {pair}")
        print(f"{'='*60}")

        cfg = get_config(pair)
        costs = get_costs(pair)
        native_t1 = cfg['tiers']['T1']['trigger']

        print(f"  Costs: spread={costs['spread_pips']}p, commission={costs['commission_pips']}p, total={costs['spread_pips']+costs['commission_pips']:.2f}p")
        print(f"  Native T1 trigger: {native_t1}")

        # ── FLOOR (native triggers) ──────────────────────────────────
        print(f"\n  [FLOOR] Running native triggers...")
        floor_result = run_backtest(pair, cfg, costs)
        if floor_result is None:
            print(f"  SKIPPED {pair} — no data")
            continue

        floor_wr = floor_result.net_win_rate
        floor_pf = floor_result.net_profit_factor
        floor_tpd = trades_per_day(floor_result)
        floor_trades = floor_result.total_trades

        print(f"  Floor: WR={floor_wr:.1f}%, PF={floor_pf:.2f}, tr/day={floor_tpd}, trades={floor_trades}")

        # ── CEILING (T1 trigger ↑ 20% steps) ────────────────────────
        print(f"\n  [CEILING] Sweeping T1 trigger upward...")
        ceiling_trigger, ceiling_result = find_ceiling(pair, cfg, costs)

        if ceiling_result and ceiling_result.total_trades > 0:
            ceil_wr = ceiling_result.net_win_rate
            ceil_pf = ceiling_result.net_profit_factor
            ceil_tpd = trades_per_day(ceiling_result)
            ceil_trades = ceiling_result.total_trades
            print(f"  Ceiling @ T1={ceiling_trigger}: WR={ceil_wr:.1f}%, PF={ceil_pf:.2f}, tr/day={ceil_tpd}, trades={ceil_trades}")
        else:
            ceiling_trigger = None
            ceil_wr = None
            ceil_pf = None
            ceil_tpd = None
            ceil_trades = None
            print(f"  Ceiling: no trades generated")

        all_results[pair] = {
            'floor': {
                't1_trigger': native_t1,
                'net_wr': floor_wr,
                'net_pf': floor_pf,
                'net_tr_per_day': floor_tpd,
                'total_trades': floor_trades,
            },
            'ceiling': {
                't1_trigger': ceiling_trigger,
                'net_wr': ceil_wr,
                'net_pf': ceil_pf,
                'net_tr_per_day': ceil_tpd,
                'total_trades': ceil_trades,
            },
            'costs': costs,
        }

    # ── SAVE JSON ────────────────────────────────────────────────────
    out_path = os.path.join(REPORTS_DIR, 'fx_gbp_cost_sweep.json')
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n\nResults saved to {out_path}")

    # ── PRINT SUMMARY TABLE ──────────────────────────────────────────
    print(f"\n{'='*90}")
    print(f"  FX-GBP BASKET COST SWEEP — SUMMARY")
    print(f"{'='*90}")
    print(f"  {'Pair':<10} | {'Floor WR':>9} | {'Floor PF':>9} | {'Floor T/D':>10} | {'Ceil WR':>9} | {'Ceil PF':>9} | {'Ceil T/D':>10}")
    print(f"  {'-'*10}-+-{'-'*9}-+-{'-'*9}-+-{'-'*10}-+-{'-'*9}-+-{'-'*9}-+-{'-'*10}")

    for pair in PAIRS:
        if pair not in all_results:
            continue
        r = all_results[pair]
        f = r['floor']
        c = r['ceiling']
        c_wr = f"{c['net_wr']:.1f}%" if c['net_wr'] is not None else "N/A"
        c_pf = f"{c['net_pf']:.2f}" if c['net_pf'] is not None else "N/A"
        c_tpd = f"{c['net_tr_per_day']:.3f}" if c['net_tr_per_day'] is not None else "N/A"
        print(f"  {pair:<10} | {f['net_wr']:>8.1f}% | {f['net_pf']:>9.2f} | {f['net_tr_per_day']:>10.3f} | {c_wr:>9} | {c_pf:>9} | {c_tpd:>10}")

    print(f"{'='*90}")


if __name__ == "__main__":
    main()
