"""
FX-USD Basket Backtest — Trading Cost Sweep (Floor & Ceiling)
==============================================================
For each pair:
  Floor = native triggers from asset_configs.py
  Ceiling = T1 trigger increased by 20% steps until WR < 81% OR PF < 10

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

PAIRS = ['USDJPY', 'USDCHF', 'USDCAD', 'NZDUSD', 'AUDUSD']

# Map pair -> CSV file
CSV_MAP = {
    'USDJPY': 'USDJPY_M5.csv',
    'USDCHF': 'USDCHF_M5.csv',
    'USDCAD': 'USDCAD_PRO_M5.csv',
    'NZDUSD': 'NZDUSD_M5.csv',
    'AUDUSD': 'AUDUSD_M5.csv',
}


def run_backtest(pair, cfg, costs, t1_trigger_override=None):
    """Run a single backtest for a pair with given config and costs."""
    csv_file = os.path.join(DATA_DIR, CSV_MAP[pair])
    if not os.path.exists(csv_file):
        print(f"  ERROR: CSV not found: {csv_file}")
        return None

    # Deep copy config so we can override triggers
    import copy as _copy
    run_cfg = _copy.deepcopy(cfg)

    # Apply T1 trigger override if specified (ceiling sweep)
    if t1_trigger_override is not None:
        run_cfg['tiers']['T1']['trigger'] = t1_trigger_override

    # AR expansion = 3.0x — multiply ar_max for all tiers
    for tier_name, tier_data in run_cfg['tiers'].items():
        tier_data['ar_max'] = tier_data['ar_max'] * 3.0

    bt = SymmetryTrapBacktest(
        pip_size=run_cfg['pip_value'],
        symbol=pair,
        config=run_cfg,
        spread_pips=costs['spread_pips'],
        commission_pips=costs['commission_pips'],
    )

    result = bt.run_from_csv(csv_file)
    return result


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    all_results = {}

    for pair in PAIRS:
        print(f"\n{'='*60}")
        print(f"  {pair}")
        print(f"{'='*60}")

        cfg = get_config(pair)
        costs = get_costs(pair)

        print(f"  Costs: spread={costs['spread_pips']}p, commission={costs['commission_pips']}p, total={costs['spread_pips']+costs['commission_pips']:.2f}p")
        print(f"  Native T1 trigger: {cfg['tiers']['T1']['trigger']}")

        # ── FLOOR: native triggers ─────────────────────────────────────
        print(f"\n  [FLOOR] Running with native triggers...")
        floor_result = run_backtest(pair, cfg, costs)

        if floor_result is None or floor_result.total_trades == 0:
            print(f"  No trades generated for {pair} floor.")
            continue

        floor_net_wr = floor_result.net_win_rate
        floor_net_pf = floor_result.net_profit_factor
        floor_days = max(floor_result.data_days, 1)
        floor_net_tr_per_day = round(floor_result.total_trades / floor_days, 3)

        print(f"  Floor: {floor_result.total_trades} tr, net WR={floor_net_wr:.1f}%, net PF={floor_net_pf:.2f}, net tr/day={floor_net_tr_per_day}")

        # ── CEILING: increase T1 trigger until WR < 81% OR PF < 10 ────
        native_t1_trigger = cfg['tiers']['T1']['trigger']
        step_pct = 0.20  # 20% steps
        ceiling_result = None
        ceiling_trigger = native_t1_trigger

        for i in range(1, 50):  # max 50 steps safety
            test_trigger = round(native_t1_trigger * (1 + step_pct * i), 4)
            print(f"\n  [CEILING] Trying T1 trigger = {test_trigger} (step {i}, +{step_pct*i*100:.0f}%)...")

            result = run_backtest(pair, cfg, costs, t1_trigger_override=test_trigger)

            if result is None or result.total_trades == 0:
                print(f"    No trades at trigger={test_trigger}. Stopping.")
                break

            net_wr = result.net_win_rate
            net_pf = result.net_profit_factor
            print(f"    Result: {result.total_trades} tr, net WR={net_wr:.1f}%, net PF={net_pf:.2f}")

            if net_wr < 81.0 or net_pf < 10.0:
                # This is the ceiling — the last viable step was the previous one
                # But we report THIS step as the ceiling (first that breaks threshold)
                ceiling_result = result
                ceiling_trigger = test_trigger
                print(f"    → CEILING FOUND at trigger={test_trigger} (WR={net_wr:.1f}%, PF={net_pf:.2f})")
                break
            else:
                # Still viable, keep going — store as best ceiling so far
                ceiling_result = result
                ceiling_trigger = test_trigger

        if ceiling_result is None:
            print(f"  No ceiling found for {pair}.")
            ceiling_net_wr = floor_net_wr
            ceiling_net_pf = floor_net_pf
            ceiling_net_tr_per_day = floor_net_tr_per_day
            ceiling_trigger = native_t1_trigger
        else:
            ceiling_net_wr = ceiling_result.net_win_rate
            ceiling_net_pf = ceiling_result.net_profit_factor
            ceiling_days = max(ceiling_result.data_days, 1)
            ceiling_net_tr_per_day = round(ceiling_result.total_trades / ceiling_days, 3)

        all_results[pair] = {
            'floor': {
                't1_trigger': native_t1_trigger,
                'net_wr': round(floor_net_wr, 1),
                'net_pf': round(floor_net_pf, 2),
                'net_tr_per_day': floor_net_tr_per_day,
                'total_trades': floor_result.total_trades,
            },
            'ceiling': {
                't1_trigger': ceiling_trigger,
                'net_wr': round(ceiling_net_wr, 1),
                'net_pf': round(ceiling_net_pf, 2),
                'net_tr_per_day': ceiling_net_tr_per_day,
                'total_trades': ceiling_result.total_trades if ceiling_result else 0,
            },
            'costs': {
                'spread_pips': costs['spread_pips'],
                'commission_pips': costs['commission_pips'],
                'total_pips': costs['spread_pips'] + costs['commission_pips'],
            }
        }

    # ── Save JSON ─────────────────────────────────────────────────────
    out_path = os.path.join(REPORTS_DIR, 'fx_usd_cost_sweep.json')
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n\nResults saved to {out_path}")

    # ── Print Summary Table ───────────────────────────────────────────
    print(f"\n{'='*90}")
    print(f"FX-USD COST SWEEP SUMMARY")
    print(f"{'='*90}")
    print(f"{'Pair':<10} {'Floor WR':>10} {'Floor PF':>10} {'Floor T/D':>10} {'Ceil WR':>10} {'Ceil PF':>10} {'Ceil T/D':>10} {'Cost(p)':>10}")
    print(f"{'-'*90}")
    for pair in PAIRS:
        if pair not in all_results:
            continue
        r = all_results[pair]
        print(f"{pair:<10} {r['floor']['net_wr']:>9.1f}% {r['floor']['net_pf']:>10.2f} {r['floor']['net_tr_per_day']:>10.3f} {r['ceiling']['net_wr']:>9.1f}% {r['ceiling']['net_pf']:>10.2f} {r['ceiling']['net_tr_per_day']:>10.3f} {r['costs']['total_pips']:>10.2f}")
    print(f"{'='*90}")


if __name__ == '__main__':
    main()
