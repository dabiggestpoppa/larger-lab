"""
CEREBUS Forex Re-SWEEP v2 — ALL 28 pairs, corrected methodology.
Passes config (for session params) + tier_config (for scaled tiers) separately.
Engine fix ensures tier_config takes priority over config["tiers"].
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

FOREX_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD", "USDCAD",
    "EURGBP", "EURJPY", "GBPJPY", "EURCHF", "AUDJPY", "NZDJPY", "AUDNZD",
    "AUDCAD", "AUDCHF", "CADJPY", "CHFJPY", "CADCHF", "EURNZD", "EURAUD",
    "EURCAD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD", "NZDCAD", "NZDCHF",
]

MULTIPLIERS = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.7, 2.0, 2.5, 3.0]

def build_scaled_tiers(pair, mult):
    """Return only the scaled tier config dict (not full config)."""
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
    csv_path = DATA_DIR / f"{pair}_M5.csv"
    if not csv_path.exists():
        candidates = sorted(DATA_DIR.glob(f"{pair}*.csv"))
        if candidates:
            csv_path = candidates[0]
        else:
            print(f"  ERROR: No CSV for {pair}")
            return []

    base_config = ASSET_CONFIGS[pair]
    base_t1 = base_config["tiers"]["T1"]["trigger"]

    # Use the config's pip_value directly
    pip_value = base_config.get("pip_value", 0.0001)

    bars, _ = load_m5_csv(str(csv_path), pip_size=pip_value)
    if not bars:
        print(f"  ERROR: No bars for {pair}")
        return []

    n_days = (bars[-1].timestamp.date() - bars[0].timestamp.date()).days
    print(f"  {pair}: {len(bars)} bars, {n_days} days, pip={pip_value}, base_t1={base_t1}")

    results = []
    for i, mult in enumerate(MULTIPLIERS):
        scaled_tiers = build_scaled_tiers(pair, mult)
        t1_trigger = round(base_t1 * mult, 1)

        t0 = time.time()
        bt = SymmetryTrapBacktest(
            pip_size=pip_value,
            tier_config=scaled_tiers,
            config=base_config,
            symbol=pair,
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
    print("CEREBUS FOREX RE-SWEEP v2 — ALL 28 PAIRS (ENGINE FIX)")
    print(f"Multipliers: {MULTIPLIERS}")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    all_results = {}
    for idx, pair in enumerate(FOREX_PAIRS):
        print(f"\n[{idx+1:2d}/{28}] {pair}")
        results = run_sweep_pair(pair)
        if results:
            all_results[pair] = results

    output_path = REPORTS_DIR / "trigger_sweep_forex_v2.json"
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n\nResults saved to: {output_path}")

    # Quick summary for EURUSD
    if "EURUSD" in all_results:
        print("\n--- EURUSD QUICK COMPARE ---")
        for e in all_results["EURUSD"]:
            print(f"  mult={e['multiplier']:.1f} t1={e['t1_trigger']:.1f} | trades={e['trades']} | WR={e['wr']:.1f}% | PF={e['pf']:.2f} | tr/d={e['tr_per_day']:.3f}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
