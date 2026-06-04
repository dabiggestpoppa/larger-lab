"""
MAX ACCURACY SWEEP — EUR Basket
================================
Sweep triggers UPWARD from native to find maximum WR.
Tracks every result for full accuracy-frequency curve.
Guardrails: PF >= 10.0, min 0.5 tr/day
"""
import sys, os, json, time

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')

# Native configs from asset_configs.py — EUR pairs
NATIVE_CONFIGS = {
    "EURUSD": {
        "csv": "EURUSD_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 20.0, "au": 10.0, "trigger": 12.0},
                  "T2": {"ar_max": 30.0, "au": 12.0, "trigger": 15.0},
                  "T3": {"ar_max": 45.0, "au": 15.0, "trigger": 19.0}},
    },
    "EURGBP": {
        "csv": "EURGBP_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 20.98, "au": 7.0, "trigger": 8.0},
                  "T2": {"ar_max": 40.33, "au": 14.0, "trigger": 17.0},
                  "T3": {"ar_max": 40.33, "au": 19.0, "trigger": 23.0}},
    },
    "EURJPY": {
        "csv": "EURJPY_PRO_M5.csv",
        "pip_value": 0.01,
        "tiers": {"T1": {"ar_max": 91.57, "au": 29.0, "trigger": 35.0},
                  "T2": {"ar_max": 160.35, "au": 63.0, "trigger": 75.0},
                  "T3": {"ar_max": 160.35, "au": 63.0, "trigger": 76.0}},
    },
    "EURAUD": {
        "csv": "EURAUD_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 77.51, "au": 27.0, "trigger": 32.0},
                  "T2": {"ar_max": 135.4, "au": 51.0, "trigger": 61.0},
                  "T3": {"ar_max": 135.4, "au": 58.0, "trigger": 69.0}},
    },
    "EURNZD": {
        "csv": "EURNZD_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 77.48, "au": 28.0, "trigger": 34.0},
                  "T2": {"ar_max": 143.25, "au": 49.0, "trigger": 59.0},
                  "T3": {"ar_max": 143.25, "au": 61.0, "trigger": 73.0}},
    },
    "EURCHF": {
        "csv": "EURCHF_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 28.55, "au": 9.0, "trigger": 11.0},
                  "T2": {"ar_max": 53.15, "au": 19.0, "trigger": 23.0},
                  "T3": {"ar_max": 53.15, "au": 22.0, "trigger": 27.0}},
    },
    "EURCAD": {
        "csv": "EURCAD_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 38.86, "au": 13.0, "trigger": 16.0},
                  "T2": {"ar_max": 75.87, "au": 25.0, "trigger": 31.0},
                  "T3": {"ar_max": 75.87, "au": 32.0, "trigger": 38.0}},
    },
}

AR_EXPANSION = 3.0
PF_FLOOR = 10.0
MIN_TR_PER_DAY = 0.5


def apply_vector_with_trigger(native_tiers, trigger_override):
    optimized = {}
    for tier_name, tier_cfg in native_tiers.items():
        if tier_name == "T1":
            t = trigger_override
        else:
            orig_t1 = native_tiers["T1"]["trigger"]
            ratio = tier_cfg["trigger"] / orig_t1
            t = round(trigger_override * ratio, 1)
        optimized[tier_name] = {
            "ar_max": round(tier_cfg["ar_max"] * AR_EXPANSION, 2),
            "au": tier_cfg["au"],
            "trigger": t,
        }
    return optimized


def run_pair_with_trigger(asset_key, native_config, t1_trigger):
    csv_path = os.path.join(DATA_DIR, native_config["csv"])
    if not os.path.exists(csv_path):
        return None
    optimized_tiers = apply_vector_with_trigger(native_config["tiers"], t1_trigger)
    bt = SymmetryTrapBacktest(
        pip_size=native_config["pip_value"],
        tier_config=optimized_tiers,
        symbol=asset_key,
        config={"pip_value": native_config["pip_value"], "tiers": optimized_tiers}
    )
    bt.session_cutoff = 16
    result = bt.run_from_csv(csv_path)
    trades = result.trades
    if not trades:
        return {"trades": 0, "wr": 0, "pnl": 0, "pf": 0, "max_dd": 0, "max_cl": 0,
                "avg_w": 0, "avg_l": 0, "exp": 0, "max_cw": 0, "days": result.data_days,
                "t1_trigger": t1_trigger, "tiers": optimized_tiers, "tr_per_day": 0}
    wins = sum(1 for t in trades if t.pnl_pips > 0)
    losses = sum(1 for t in trades if t.pnl_pips < 0)
    wr = wins / len(trades) * 100
    max_cw = max_cl = cur_w = cur_l = 0
    for t in trades:
        if t.pnl_pips > 0:
            cur_w += 1; cur_l = 0; max_cw = max(max_cw, cur_w)
        elif t.pnl_pips < 0:
            cur_l += 1; cur_w = 0; max_cl = max(max_cl, cur_l)
        else:
            cur_w = cur_l = 0
    tr_per_day = len(trades) / result.data_days if result.data_days else 0
    return {
        "trades": len(trades), "days": result.data_days, "wr": wr,
        "pnl": result.total_pnl_pips, "pf": result.profit_factor,
        "avg_w": result.avg_win_pips, "avg_l": result.avg_loss_pips,
        "exp": result.expectancy_pips, "max_dd": result.max_drawdown_pips,
        "max_cw": max_cw, "max_cl": max_cl, "t1_trigger": t1_trigger,
        "tiers": optimized_tiers, "tr_per_day": tr_per_day,
    }


def sweep_pair(asset_key):
    native = NATIVE_CONFIGS[asset_key]
    csv_path = os.path.join(DATA_DIR, native["csv"])
    if not os.path.exists(csv_path):
        print("  {}: MISSING DATA".format(asset_key), flush=True)
        return []
    native_t1 = native["tiers"]["T1"]["trigger"]
    # Coarse sweep UP: native, native+2, native+4, ... up to 2x native or until trades < 0.5/day
    coarse_triggers = []
    t = native_t1
    max_t = native_t1 * 2.0
    while t <= max_t:
        coarse_triggers.append(round(t, 1))
        t += 2.0
    print("  {}: Coarse sweep UP {} triggers ({} to {})".format(
        asset_key, len(coarse_triggers), min(coarse_triggers), max(coarse_triggers)), flush=True)
    results = []
    peak_wr = 0
    peak_trigger = None
    peak_tr_per_day = 0
    for t1 in coarse_triggers:
        r = run_pair_with_trigger(asset_key, native, t1)
        if r is None: continue
        results.append(r)
        status = "OK" if r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY else "FAIL"
        print("    T1={:>6} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | {:>7.1f}p PnL | MaxDD {:>5.1f}p | MaxCL {} | Tr/d {:>4.2f} | {}".format(
            t1, r["trades"], r["wr"], r["pf"], r["pnl"], r["max_dd"], r["max_cl"],
            r["tr_per_day"], status), flush=True)
        if r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY:
            if r["wr"] > peak_wr:
                peak_wr = r["wr"]
                peak_trigger = t1
                peak_tr_per_day = r["tr_per_day"]
            elif r["wr"] == peak_wr and r["tr_per_day"] > peak_tr_per_day:
                peak_trigger = t1
                peak_tr_per_day = r["tr_per_day"]
        # If trades drop below minimum, stop sweeping
        if r["tr_per_day"] < MIN_TR_PER_DAY:
            print("    -> Tr/d below 0.5 floor, stopping coarse sweep", flush=True)
            break
    if peak_trigger is None:
        print("  {}: No valid config found!".format(asset_key), flush=True)
        return results
    print("  {}: Peak WR={:.1f}% at T1={}. Fine sweep around peak...".format(
        asset_key, peak_wr, peak_trigger), flush=True)
    # Fine sweep: +/- 2 around peak in 1.0 steps
    fine_start = max(native_t1, peak_trigger - 3.0)
    fine_end = peak_trigger + 3.0
    t = fine_start
    while t <= fine_end:
        t = round(t, 1)
        if t in [r["t1_trigger"] for r in results]:
            t += 1.0
            continue
        r = run_pair_with_trigger(asset_key, native, t)
        if r:
            results.append(r)
            status = "OK" if r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY else "FAIL"
            print("    T1={:>6} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | Tr/d {:>4.2f} | {}".format(
                t, r["trades"], r["wr"], r["pf"], r["tr_per_day"], status), flush=True)
            if r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY:
                if r["wr"] > peak_wr or (r["wr"] == peak_wr and r["tr_per_day"] > peak_tr_per_day):
                    peak_wr = r["wr"]
                    peak_trigger = t
                    peak_tr_per_day = r["tr_per_day"]
        t += 1.0
    # Binary search between peak and the trigger just below peak for precision
    # Find the trigger just below peak_trigger that has lower WR
    lower_candidates = [r for r in results if r["t1_trigger"] < peak_trigger and r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY]
    upper_candidates = [r for r in results if r["t1_trigger"] > peak_trigger and r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY]
    lower_bound = max([r["t1_trigger"] for r in lower_candidates], default=native_t1) if lower_candidates else native_t1
    upper_bound = min([r["t1_trigger"] for r in upper_candidates], default=peak_trigger + 2.0) if upper_candidates else peak_trigger + 2.0
    print("  {}: Binary search between {} and {} (peak WR={:.1f}% at T1={})".format(
        asset_key, lower_bound, upper_bound, peak_wr, peak_trigger), flush=True)
    for _ in range(4):
        mid = round((lower_bound + upper_bound) / 2, 2)
        if mid == lower_bound or mid == upper_bound: break
        if mid in [r["t1_trigger"] for r in results]:
            # Already tested, find nearest untested
            break
        r = run_pair_with_trigger(asset_key, native, mid)
        if r:
            results.append(r)
            status = "OK" if r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY else "FAIL"
            print("    T1={:>6} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | Tr/d {:>4.2f} | {}".format(
                mid, r["trades"], r["wr"], r["pf"], r["tr_per_day"], status), flush=True)
            if r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY:
                if r["wr"] > peak_wr or (r["wr"] == peak_wr and r["tr_per_day"] > peak_tr_per_day):
                    peak_wr = r["wr"]
                    peak_trigger = mid
                    peak_tr_per_day = r["tr_per_day"]
                    lower_bound = mid
                else:
                    upper_bound = mid
            else:
                upper_bound = mid
    # Find best valid result
    valid = [r for r in results if r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY]
    if valid:
        best = max(valid, key=lambda r: (r["wr"], r["tr_per_day"]))
        print("  {} [BEST] T1={} | {}tr | {:.1f}% WR | PF {:.2f} | PnL {:.1f}p | MaxDD {:.1f}p | MaxCL {} | Tr/d {:.2f}".format(
            asset_key, best["t1_trigger"], best["trades"], best["wr"], best["pf"],
            best["pnl"], best["max_dd"], best["max_cl"], best["tr_per_day"]), flush=True)
    print("  {} total runs: {}".format(asset_key, len(results)), flush=True)
    return results


if __name__ == '__main__':
    print("=" * 80)
    print("MAX ACCURACY SWEEP — EUR Basket")
    print("AR Expansion: 3.0x | Cutoff: 4PM EST | PF Floor: 10.0 | Min Tr/Day: 0.5")
    print("=" * 80)
    all_results = {}
    for asset in ["EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD"]:
        print("\n--- {} ---".format(asset))
        all_results[asset] = sweep_pair(asset)
    out_path = os.path.join(QUANTLAB_ROOT, 'reports', 'trigger_sweep_max_accuracy_eur.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    serializable = {}
    for asset, results in all_results.items():
        serializable[asset] = []
        for r in results:
            rd = dict(r); rd.pop('tiers', None); serializable[asset].append(rd)
    with open(out_path, 'w') as f:
        json.dump(serializable, f, indent=2, default=str)
    print("\nResults saved to: {}".format(out_path))
    print("\n" + "=" * 80)
    print("SUMMARY — EUR Basket (Max Accuracy)")
    print("=" * 80)
    print("{:<10} {:>6} {:>8} {:>10} {:>8} {:>8} {:>6} {:>8}".format(
        "Asset", "Trades", "WR%", "PnL", "PF", "MaxDD", "MaxCL", "Tr/Day"))
    print("-" * 80)
    total_trades = 0
    for asset in ["EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD"]:
        if all_results[asset]:
            valid = [r for r in all_results[asset] if r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY]
            if valid:
                best = max(valid, key=lambda r: (r["wr"], r["tr_per_day"]))
                print("{:<10} {:>6} {:>7.1f}% {:>10.1f} {:>8.2f} {:>8.1f} {:>6} {:>8.2f}".format(
                    asset, best["trades"], best["wr"], best["pnl"], best["pf"],
                    best["max_dd"], best["max_cl"], best["tr_per_day"]))
                total_trades += best["trades"]
    print("-" * 80)
    print("{:<10} {:>6}".format("TOTAL", total_trades))
