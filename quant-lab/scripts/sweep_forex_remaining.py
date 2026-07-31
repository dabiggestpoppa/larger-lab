"""
CEREBUS Forex Re-SWEEP — RESUME from pair 14 (AUDNZD)
Continues the full 28-pair sweep that was killed mid-run.
"""
import sys, json, os, time
from pathlib import Path

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

# Remaining pairs (14 through 28)
REMAINING_PAIRS = [
    "AUDNZD", "AUDCAD", "AUDCHF", "CADJPY", "CHFJPY", "CADCHF",
    "EURNZD", "EURAUD", "EURCAD", "GBPAUD", "GBPCAD", "GBPCHF",
    "GBPNZD", "NZDCAD", "NZDCHF",
]

MULTIPLIERS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.7, 2.0, 2.5, 3.0]

PIP_VALUES = {
    "BTCUSD": 1.0, "ETHUSD": 1.0,
    "XAUUSD": 0.10, "XAGUSD": 0.10,
    "US500": 1.0, "DE30": 1.0, "FR40": 1.0, "HK50": 1.0,
}
DEFAULT_PIP = 0.10

def get_pip_val(pair):
    return PIP_VALUES.get(pair, 0.07 if "JPY" in pair else DEFAULT_PIP)

def build_scaled_config(pair, mult):
    base = ASSET_CONFIGS[pair].copy()
    tiers = {}
    for tn in ["T1", "T2", "T3"]:
        t = base["tiers"][tn]
        tiers[tn] = {
            "ar_max": round(t["ar_max"] * mult, 1),
            "au": round(t["au"] * mult, 1),
            "trigger": round(t["trigger"] * mult, 1),
        }
    base["tiers"] = tiers
    return base

def run_sweep_pair(pair):
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
        scaled_config = build_scaled_config(pair, mult)
        t1_trigger = round(base_t1 * mult, 1)

        t0 = time.time()
        bt = SymmetryTrapBacktest(
            pip_size=pip_value,
            symbol=pair,
            config=scaled_config,
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
    print("CEREBUS FOREX RE-SWEEP — RESUME (pairs 14-28)")
    print(f"Remaining: {REMAINING_PAIRS}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    all_results = {}
    for idx, pair in enumerate(REMAINING_PAIRS):
        print(f"\n[{idx+1:2d}/{len(REMAINING_PAIRS)}] {pair}")
        results = run_sweep_pair(pair)
        if results:
            all_results[pair] = results

    # Save partial results
    output_path = REPORTS_DIR / "trigger_sweep_forex_remaining.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n\nRemaining results saved to: {output_path}")
    print(f"Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
