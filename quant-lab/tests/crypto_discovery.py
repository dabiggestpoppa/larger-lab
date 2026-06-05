"""
CRYPTO RAW DISCOVERY — BNB, SOL, LTC, BCH, XLM
================================================
Quick volatility scan to estimate AU/trigger/ar_max for each pair.
Runs native-like configs and reports trade count + WR.
Uses same engine as FX sweep (symmetry_trap_backtest).

Usage:
  python crypto_discovery.py
"""
import sys, os, json, time

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')
REPORTS_DIR = os.path.join(QUANTLAB_ROOT, 'reports')

# ─── INITIAL CRYPTO CONFIGS (estimated from price levels) ──────────────
# pip_value = 1.0 for all (engine convention)
# AU estimated from typical Asian session range
# trigger = 1.2x AU, ar_max = 2x AU (same ratio as FX)
# These are ROUGH estimates — discovery will calibrate

DISCOVERY_CONFIGS = {
    "BNBUSD": {
        "csv": "BNBUSD_M5.csv",
        "pip_value": 1.0,
        "sl_buffer": 5.0,
        # BNB ~$609, daily range ~$10-30, Asian range ~$3-8
        "tiers": {
            "T1": {"ar_max": 30.0, "au": 10.0, "trigger": 12.0},
            "T2": {"ar_max": 60.0, "au": 20.0, "trigger": 24.0},
            "T3": {"ar_max": 120.0, "au": 40.0, "trigger": 48.0},
        },
        "test_triggers": [6, 8, 10, 12, 15, 18, 20, 25, 30],
    },
    "SOLUSD": {
        "csv": "SOLUSD_M5.csv",
        "pip_value": 1.0,
        "sl_buffer": 3.0,
        # SOL ~$69, daily range ~$2-8, Asian range ~$0.5-2
        "tiers": {
            "T1": {"ar_max": 15.0, "au": 5.0, "trigger": 6.0},
            "T2": {"ar_max": 30.0, "au": 10.0, "trigger": 12.0},
            "T3": {"ar_max": 60.0, "au": 20.0, "trigger": 24.0},
        },
        "test_triggers": [3, 4, 5, 6, 8, 10, 12, 15, 20],
    },
    "LTCUSD": {
        "csv": "LTCUSD_M5.csv",
        "pip_value": 1.0,
        "sl_buffer": 3.0,
        # LTC ~$46, daily range ~$1-4, Asian range ~$0.3-1
        "tiers": {
            "T1": {"ar_max": 10.0, "au": 3.5, "trigger": 4.2},
            "T2": {"ar_max": 20.0, "au": 7.0, "trigger": 8.4},
            "T3": {"ar_max": 40.0, "au": 14.0, "trigger": 16.8},
        },
        "test_triggers": [2, 3, 4, 5, 6, 8, 10, 12, 15],
    },
    "BCHUSD": {
        "csv": "BCHUSD_M5.csv",
        "pip_value": 1.0,
        "sl_buffer": 5.0,
        # BCH ~$250, daily range ~$5-20, Asian range ~$2-5
        "tiers": {
            "T1": {"ar_max": 20.0, "au": 7.0, "trigger": 8.4},
            "T2": {"ar_max": 40.0, "au": 14.0, "trigger": 16.8},
            "T3": {"ar_max": 80.0, "au": 28.0, "trigger": 33.6},
        },
        "test_triggers": [4, 6, 8, 10, 12, 15, 18, 20, 25],
    },
    "XLMUSD": {
        "csv": "XLMUSD_M5.csv",
        "pip_value": 1.0,
        "sl_buffer": 2.0,
        # XLM ~$0.21, daily range ~$0.01-0.05, Asian range ~$0.003-0.01
        # Very small price → need tiny AU
        "tiers": {
            "T1": {"ar_max": 0.08, "au": 0.03, "trigger": 0.036},
            "T2": {"ar_max": 0.16, "au": 0.06, "trigger": 0.072},
            "T3": {"ar_max": 0.32, "au": 0.12, "trigger": 0.144},
        },
        "test_triggers": [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.15],
    },
}

AR_EXPANSION = 3.0


def apply_vector_with_trigger(native_tiers, trigger_override):
    optimized = {}
    for tier_name, tier_cfg in native_tiers.items():
        if tier_name == "T1":
            t = trigger_override
        else:
            orig_t1 = native_tiers["T1"]["trigger"]
            ratio = tier_cfg["trigger"] / orig_t1
            t = round(trigger_override * ratio, 4)
        optimized[tier_name] = {
            "ar_max": round(tier_cfg["ar_max"] * AR_EXPANSION, 4),
            "au": tier_cfg["au"],
            "trigger": t,
        }
    return optimized


def run_pair_with_trigger(asset_key, config, t1_trigger):
    csv_path = os.path.join(DATA_DIR, config["csv"])
    if not os.path.exists(csv_path):
        return None

    optimized_tiers = apply_vector_with_trigger(config["tiers"], t1_trigger)

    bt = SymmetryTrapBacktest(
        pip_size=config["pip_value"],
        tier_config=optimized_tiers,
        symbol=asset_key,
        config={"pip_value": config["pip_value"], "tiers": optimized_tiers, "name": asset_key}
    )
    bt.session_cutoff = 16

    result = bt.run_from_csv(csv_path)
    trades = result.trades

    if not trades:
        return {"trades": 0, "wr": 0, "pnl": 0, "pf": 0, "max_dd": 0, "days": result.data_days, "t1_trigger": t1_trigger, "tr_per_day": 0}

    wins = sum(1 for t in trades if t.pnl_pips > 0)
    losses = sum(1 for t in trades if t.pnl_pips < 0)
    wr = wins / len(trades) * 100
    tr_per_day = len(trades) / result.data_days if result.data_days else 0

    return {
        "trades": len(trades), "days": result.data_days, "wr": wr,
        "pnl": result.total_pnl_pips, "pf": result.profit_factor,
        "max_dd": result.max_drawdown_pips, "t1_trigger": t1_trigger,
        "tr_per_day": tr_per_day,
    }


if __name__ == '__main__':
    print("=" * 100, flush=True)
    print("CRYPTO RAW DISCOVERY — BNB, SOL, LTC, BCH, XLM", flush=True)
    print("=" * 100, flush=True)

    all_results = {}

    for asset, config in DISCOVERY_CONFIGS.items():
        csv_path = os.path.join(DATA_DIR, config["csv"])
        if not os.path.exists(csv_path):
            print(f"\n{asset}: MISSING DATA — skipping", flush=True)
            continue

        print(f"\n{'=' * 100}", flush=True)
        print(f">>> {asset}", flush=True)
        print(f"{'=' * 100}", flush=True)

        results = []
        for t1 in config["test_triggers"]:
            r = run_pair_with_trigger(asset, config, t1)
            if r is None:
                continue
            results.append(r)
            flag = "OK" if r["wr"] >= 81 else "LOW" if r["wr"] > 0 else "ZERO"
            print("  T1={:>8} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | {:>8.1f}p | Tr/d {:>4.2f} | {}".format(
                t1, r["trades"], r["wr"], r["pf"], r["pnl"], r["tr_per_day"], flag), flush=True)

        all_results[asset] = results

        # Find best
        valid = [r for r in results if r["wr"] >= 81 and r["pf"] >= 10]
        if valid:
            best = max(valid, key=lambda r: (r["tr_per_day"], r["wr"]))
            print(f"  [BEST] T1={best['t1_trigger']} | {best['trades']}tr | {best['wr']:.1f}% WR | PF {best['pf']:.2f} | Tr/d {best['tr_per_day']:.2f}", flush=True)
        else:
            # Find highest WR
            if results:
                best_wr = max(results, key=lambda r: r["wr"])
                print(f"  [NO VALID] Best WR: T1={best_wr['t1_trigger']} | {best_wr['wr']:.1f}% WR | {best_wr['trades']}tr", flush=True)

    # Summary
    print(f"\n{'=' * 100}", flush=True)
    print("DISCOVERY SUMMARY", flush=True)
    print(f"{'=' * 100}", flush=True)
    print("{:<10} {:>8} {:>6} {:>8} {:>8} {:>10} {:>8}".format(
        "Asset", "Best_T1", "Trades", "WR%", "PF", "PnL(p)", "Tr/Day"), flush=True)
    print("-" * 70, flush=True)
    for asset, results in all_results.items():
        valid = [r for r in results if r["wr"] >= 81 and r["pf"] >= 10]
        if valid:
            best = max(valid, key=lambda r: (r["tr_per_day"], r["wr"]))
        elif results:
            best = max(results, key=lambda r: r["wr"])
        else:
            continue
        print("{:<10} {:>8} {:>6} {:>7.1f}% {:>8.2f} {:>10.1f} {:>8.2f}".format(
            asset, best["t1_trigger"], best["trades"], best["wr"], best["pf"],
            best["pnl"], best["tr_per_day"]), flush=True)

    # Save
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, 'crypto_discovery_raw.json')
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to: {out_path}", flush=True)
