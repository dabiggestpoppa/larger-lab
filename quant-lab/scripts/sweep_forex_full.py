"""
CEREBUS Forex Re-Sweep — ALL 28 pairs, corrected pip values.
Same methodology as metals/indices sweep: multipliers 0.3x–3.0x from baseline.
Uses SymmetryTrapBacktest for reliable simulation.
"""
import sys, json, os, io, time, pickle
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"
REPORTS_DIR = QUANT_LAB / "reports"
CONFIGS_DIR = QUANT_LAB / "configs"
ENGINES_DIR = QUANT_LAB / "engines"

sys.path.insert(0, str(CONFIGS_DIR))
sys.path.insert(0, str(ENGINES_DIR))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

# All 28 forex pairs
FOREX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
    "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY", "NZDJPY", "AUDNZD",
    "AUDCAD", "AUDCHF", "CADJPY", "CHFJPY", "CADCHF", "EURNZD", "EURAUD",
    "EURCAD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD", "NZDCAD", "NZDCHF",
]

# Multiplier range (same as metals/indices sweep)
MULTIPLIERS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.7, 2.0, 2.5, 3.0]

# Corrected pip values
PIP_VALUES = {
    "BTCUSD": 1.0, "ETHUSD": 1.0,
    "XAUUSD": 0.10, "XAGUSD": 0.10,
    "US500": 1.0, "DE30": 1.0, "FR40": 1.0, "HK50": 1.0,
}
DEFAULT_PIP = 0.10


def get_pip_val(pair):
    return PIP_VALUES.get(pair, 0.07 if "JPY" in pair else DEFAULT_PIP)


def build_scaled_config(pair, mult):
    """Scale tier config by multiplier from baseline."""
    base = ASSET_CONFIGS[pair]
    tiers = {}
    for tn in ["T1", "T2", "T3"]:
        t = base["tiers"][tn]
        tiers[tn] = {
            "ar_max": round(t["ar_max"] * mult, 1),
            "au": round(t["au"] * mult, 1),
            "trigger": round(t["trigger"] * mult, 1),
        }
    return tiers


def run_sweep_pair(pair):
    """Run full trigger sweep for a single forex pair."""
    csv_path = DATA_DIR / f"{pair}_M5.csv"
    if not csv_path.exists():
        candidates = sorted(DATA_DIR.glob(f"{pair}*.csv"))
        if candidates:
            csv_path = candidates[0]
        else:
            print(f"  ERROR: No CSV for {pair}")
            return []

    base_config = ASSET_CONFIGS[pair]
    pip_value = get_pip_val(pair)
    base_t1 = base_config["tiers"]["T1"]["trigger"]

    bars, _ = load_m5_csv(str(csv_path), pip_size=pip_value)
    if not bars:
        print(f"  ERROR: No bars for {pair}")
        return []

    n_days = (bars[-1].timestamp.date() - bars[0].timestamp.date()).days
    print(f"  {pair}: {len(bars)} bars, {n_days} days, pip={pip_value}, base_t1={base_t1}")

    results = []
    for i, mult in enumerate(MULTIPLIERS):
        tier_config = build_scaled_config(pair, mult)
        t1_trigger = round(base_t1 * mult, 1)

        t0 = time.time()
        bt = SymmetryTrapBacktest(
            pip_size=pip_value,
            tier_config=tier_config,
            symbol=pair,
            config=None,  # FIXED: don't pass config to avoid tier override
        )
        result = bt.run(bars)
        elapsed = time.time() - t0

        if result.total_trades == 0:
            print(f"    [{i+1:2d}/{len(MULTIPLIERS)}] mult={mult:.1f} t1={t1_trigger:8.1f} | 0 trades ({elapsed:.1f}s)")
            continue

        tr_per_day = result.total_trades / n_days if n_days > 0 else 0
        pf = result.profit_factor if result.profit_factor != float("inf") else 999.99

        entry = {
            "trades": result.total_trades,
            "days": n_days,
            "wr": round(result.win_rate, 2),
            "pnl": round(result.total_pnl_pips, 1),
            "pf": round(pf, 2),
            "avg_w": round(result.avg_win_pips, 2),
            "avg_l": round(result.avg_loss_pips, 2),
            "exp": round(result.expectancy_pips, 2),
            "max_dd": round(result.max_drawdown_pips, 1),
            "max_cw": result.max_consec_wins,
            "max_cl": result.max_consec_losses,
            "t1_trigger": t1_trigger,
            "tr_per_day": round(tr_per_day, 4),
            "multiplier": mult,
        }
        results.append(entry)

        print(f"    [{i+1:2d}/{len(MULTIPLIERS)}] mult={mult:.1f} t1={t1_trigger:8.1f} | "
              f"trades={result.total_trades:5d} | WR={result.win_rate:5.1f}% | PF={pf:6.2f} | "
              f"pnl={result.total_pnl_pips:10.1f} | tr/d={tr_per_day:.3f} | {elapsed:.1f}s")

    return results


def main():
    print("=" * 70)
    print("CEREBUS FOREX RE-SWEEP — ALL 28 PAIRS")
    print(f"Multipliers: {MULTIPLIERS}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    all_results = {}
    for idx, pair in enumerate(FOREX_PAIRS):
        print(f"\n[{idx+1:2d}/{len(FOREX_PAIRS)}] {pair}")
        results = run_sweep_pair(pair)
        if results:
            all_results[pair] = results

    # Save
    output_path = REPORTS_DIR / "trigger_sweep_forex_full.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n\nResults saved to: {output_path}")

    # Summary
    print("\n" + "=" * 70)
    print("SWEEP SUMMARY")
    print("=" * 70)
    for pair, entries in all_results.items():
        if not entries:
            continue
        best_trades = max(entries, key=lambda e: e["trades"])
        best_wr = max(entries, key=lambda e: e["wr"])
        best_pf = max(entries, key=lambda e: e["pf"] if e["pf"] < 999 else 0)
        best_pnl = max(entries, key=lambda e: e["pnl"])
        print(f"\n{pair}:")
        print(f"  Max Trades: mult={best_trades['multiplier']:.1f} t1={best_trades['t1_trigger']:.1f} | "
              f"trades={best_trades['trades']} | WR={best_trades['wr']:.1f}% | "
              f"PF={best_trades['pf']:.2f} | tr/d={best_trades['tr_per_day']:.3f}")
        print(f"  Max WR:     mult={best_wr['multiplier']:.1f} t1={best_wr['t1_trigger']:.1f} | "
              f"trades={best_wr['trades']} | WR={best_wr['wr']:.1f}% | "
              f"PF={best_wr['pf']:.2f} | tr/d={best_wr['tr_per_day']:.3f}")
        print(f"  Max PF:     mult={best_pf['multiplier']:.1f} t1={best_pf['t1_trigger']:.1f} | "
              f"trades={best_pf['trades']} | WR={best_pf['wr']:.1f}% | "
              f"PF={best_pf['pf']:.2f} | tr/d={best_pf['tr_per_day']:.3f}")
        print(f"  Max PnL:    mult={best_pnl['multiplier']:.1f} t1={best_pnl['t1_trigger']:.1f} | "
              f"trades={best_pnl['trades']} | WR={best_pnl['wr']:.1f}% | "
              f"PF={best_pnl['pf']:.2f} | tr/d={best_pnl['tr_per_day']:.3f}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
