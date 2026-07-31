"""
FX CHF/JPY Basket — Floor vs Ceiling Cost Sweep
================================================
For each pair: run native (floor) triggers, then increase T1 trigger
until WR < 81% OR PF < 10 (ceiling).

AR expansion = 3.0x, session cutoff = 4PM EST (16:00).
"""

import sys
import os
import json
import copy

QUANTLAB_ROOT = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab'
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv, compute_stats
from trading_costs import get_costs
from asset_configs import get_config

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')
REPORTS_DIR = os.path.join(QUANTLAB_ROOT, 'reports')

PAIRS = ['CHFJPY', 'CADJPY', 'AUDJPY', 'NZDJPY']

# Map pair -> CSV filename
CSV_MAP = {
    'CHFJPY': 'CHFJPY_M5.csv',
    'CADJPY': 'CADJPY_PRO_M5.csv',
    'AUDJPY': 'AUDJPY_PRO_M5.csv',
    'NZDJPY': 'NZDJPY_PRO_M5.csv',
}


def run_backtest(pair, cfg, costs, t1_trigger_override=None):
    """Run a single backtest for a pair with given config and costs."""
    csv_file = os.path.join(DATA_DIR, CSV_MAP[pair])
    if not os.path.exists(csv_file):
        print(f"  ERROR: CSV not found: {csv_file}", flush=True)
        return None

    # Deep copy config so we can override triggers
    cfg_copy = copy.deepcopy(cfg)
    if t1_trigger_override is not None:
        cfg_copy['tiers']['T1']['trigger'] = t1_trigger_override

    bt = SymmetryTrapBacktest(
        pip_size=cfg_copy['pip_value'],
        config=cfg_copy,
        spread_pips=costs['spread_pips'],
        commission_pips=costs['commission_pips'],
    )
    result = bt.run_from_csv(csv_file)
    return result


def find_ceiling(pair, cfg, costs):
    """
    Increase T1 trigger by 20% steps until net WR < 81% OR net PF < 10.
    Returns (ceiling_trigger, result_at_ceiling).
    """
    native_t1 = cfg['tiers']['T1']['trigger']
    step_pct = 0.20  # 20% increments

    # Start at native, then increase
    multiplier = 1.0 + step_pct  # first step = 1.2x native
    best_result = None
    best_trigger = None

    for i in range(20):  # max 20 steps safety
        trigger_val = round(native_t1 * multiplier, 1)
        print(f"    Ceiling step {i+1}: T1 trigger = {trigger_val} (native={native_t1}, mult={multiplier:.2f})", flush=True)

        result = run_backtest(pair, cfg, costs, t1_trigger_override=trigger_val)
        if result is None or result.total_trades == 0:
            print(f"      No trades at trigger={trigger_val}, stopping.", flush=True)
            break

        net_wr = result.net_win_rate
        net_pf = result.net_profit_factor
        print(f"      Net WR={net_wr:.1f}%, Net PF={net_pf:.2f}, Trades={result.total_trades}", flush=True)

        # Check stopping condition
        if net_wr < 81.0 or net_pf < 10.0:
            print(f"    CEILING FOUND at T1={trigger_val} (WR={net_wr:.1f}%, PF={net_pf:.2f})", flush=True)
            return trigger_val, result

        best_result = result
        best_trigger = trigger_val
        multiplier += step_pct

    # If we never hit the ceiling, return the last tested
    if best_result is not None:
        print(f"    No ceiling found within 20 steps. Last tested: T1={best_trigger}", flush=True)
        return best_trigger, best_result
    return native_t1, None


def trades_per_day(result):
    """Calculate average trades per day."""
    if result.data_days == 0:
        return 0.0
    return round(result.total_trades / result.data_days, 2)


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    all_results = {}

    for pair in PAIRS:
        print(f"\n{'='*60}", flush=True)
        print(f"  PAIR: {pair}", flush=True)
        print(f"{'='*60}", flush=True)

        cfg = get_config(pair)
        costs = get_costs(pair)

        print(f"  Native T1 trigger: {cfg['tiers']['T1']['trigger']}", flush=True)
        print(f"  Costs: spread={costs['spread_pips']}p, commission={costs['commission_pips']}p, total={costs['spread_pips']+costs['commission_pips']:.2f}p", flush=True)

        # ── FLOOR: native triggers ──
        print(f"\n  [FLOOR] Running native triggers...", flush=True)
        floor_result = run_backtest(pair, cfg, costs)
        if floor_result is None:
            print(f"  SKIPPING {pair} — backtest failed", flush=True)
            continue

        floor_wr = floor_result.net_win_rate
        floor_pf = floor_result.net_profit_factor
        floor_tpd = trades_per_day(floor_result)
        print(f"  FLOOR: Net WR={floor_wr:.1f}%, Net PF={floor_pf:.2f}, Tr/day={floor_tpd}, Trades={floor_result.total_trades}", flush=True)

        # ── CEILING: increase T1 trigger ──
        print(f"\n  [CEILING] Sweeping T1 trigger upward...", flush=True)
        ceiling_trigger, ceiling_result = find_ceiling(pair, cfg, costs)

        if ceiling_result is not None:
            ceiling_wr = ceiling_result.net_win_rate
            ceiling_pf = ceiling_result.net_profit_factor
            ceiling_tpd = trades_per_day(ceiling_result)
        else:
            ceiling_wr = 0
            ceiling_pf = 0
            ceiling_tpd = 0

        print(f"  CEILING: T1={ceiling_trigger}, Net WR={ceiling_wr:.1f}%, Net PF={ceiling_pf:.2f}, Tr/day={ceiling_tpd}", flush=True)

        all_results[pair] = {
            'floor': {
                't1_trigger': cfg['tiers']['T1']['trigger'],
                'net_wr': floor_wr,
                'net_pf': floor_pf,
                'net_tr_per_day': floor_tpd,
                'total_trades': floor_result.total_trades,
                'net_pnl_pips': floor_result.net_pnl_pips,
                'net_sharpe': floor_result.net_sharpe_ratio,
                'net_max_dd_pips': floor_result.net_max_drawdown_pips,
            },
            'ceiling': {
                't1_trigger': ceiling_trigger,
                'net_wr': ceiling_wr,
                'net_pf': ceiling_pf,
                'net_tr_per_day': ceiling_tpd,
                'total_trades': ceiling_result.total_trades if ceiling_result else 0,
                'net_pnl_pips': ceiling_result.net_pnl_pips if ceiling_result else 0,
                'net_sharpe': ceiling_result.net_sharpe_ratio if ceiling_result else 0,
                'net_max_dd_pips': ceiling_result.net_max_drawdown_pips if ceiling_result else 0,
            },
            'costs': costs,
        }

    # ── Save JSON ──
    json_path = os.path.join(REPORTS_DIR, 'fx_chfjpy_cost_sweep.json')
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n\nResults saved to {json_path}", flush=True)

    # ── Print Summary Table ──
    print(f"\n{'='*90}", flush=True)
    print(f"FX CHF/JPY BASKET — COST SWEEP SUMMARY", flush=True)
    print(f"{'='*90}", flush=True)
    print(f"{'Pair':<10} {'Level':<10} {'T1 Trig':<10} {'Net WR%':<10} {'Net PF':<10} {'Tr/Day':<10} {'Trades':<10} {'Net PnL':<12} {'Net Sharpe':<12}", flush=True)
    print(f"{'-'*90}", flush=True)
    for pair in PAIRS:
        if pair not in all_results:
            continue
        r = all_results[pair]
        f = r['floor']
        c = r['ceiling']
        print(f"{pair:<10} {'FLOOR':<10} {f['t1_trigger']:<10} {f['net_wr']:<10.1f} {f['net_pf']:<10.2f} {f['net_tr_per_day']:<10} {f['total_trades']:<10} {f['net_pnl_pips']:<12.1f} {f['net_sharpe']:<12.2f}", flush=True)
        print(f"{'':<10} {'CEILING':<10} {c['t1_trigger']:<10} {c['net_wr']:<10.1f} {c['net_pf']:<10.2f} {c['net_tr_per_day']:<10} {c['total_trades']:<10} {c['net_pnl_pips']:<12.1f} {c['net_sharpe']:<12.2f}", flush=True)
        print(f"{'-'*90}", flush=True)
    print(flush=True)


if __name__ == "__main__":
    main()
