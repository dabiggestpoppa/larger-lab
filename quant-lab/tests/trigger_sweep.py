"""
TRIGGER SWEEP — Find max trades before WR < 81%
================================================
For each EUR pair, sweep T1 trigger downward from optimized value
to find the breakpoint where WR crosses below 81%.

Strategy: Coarse sweep first (step=1.0), then fine-tune around the boundary.
Reports: trigger, trades, WR, PF, MaxDD, Tr/Day for each step.
"""
import sys, os, json

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')

# ── NATIVE CONFIGS ──────────────────────────────────────────────────────
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

# ── VECTOR CONSTANTS ────────────────────────────────────────────────────
AR_EXPANSION = 3.0
WR_FLOOR = 81.0  # MAD directive: don't go below 81%


def apply_vector_with_trigger(native_tiers, trigger_override):
    """Apply vector with a specific T1 trigger override."""
    optimized = {}
    for tier_name, tier_cfg in native_tiers.items():
        if tier_name == "T1":
            t = trigger_override
        else:
            # Keep T2/T3 proportional to original T1 ratio
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
    """Run a single pair with a specific T1 trigger value."""
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
    bt.session_cutoff = 16  # 4PM EST

    result = bt.run_from_csv(csv_path)
    trades = result.trades

    if not trades:
        return {"trades": 0, "wr": 0, "pnl": 0, "pf": 0, "max_dd": 0, "max_cl": 0, "days": result.data_days}

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

    return {
        "trades": len(trades),
        "days": result.data_days,
        "wr": wr,
        "pnl": result.total_pnl_pips,
        "pf": result.profit_factor,
        "avg_w": result.avg_win_pips,
        "avg_l": result.avg_loss_pips,
        "exp": result.expectancy_pips,
        "max_dd": result.max_drawdown_pips,
        "max_cw": max_cw,
        "max_cl": max_cl,
        "t1_trigger": t1_trigger,
    }


def sweep_pair(asset_key):
    """Sweep T1 trigger to find max trades with WR >= 81%."""
    native = NATIVE_CONFIGS[asset_key]
    csv_path = os.path.join(DATA_DIR, native["csv"])
    if not os.path.exists(csv_path):
        print("  {}: MISSING DATA".format(asset_key))
        return []

    # Start from optimized trigger (native * 0.833) and go down
    opt_trigger = round(native["tiers"]["T1"]["trigger"] * 0.833, 1)
    
    # Determine sweep range: from opt_trigger down to 1.0
    # For JPY pairs, step = 1.0; for others step = 0.5
    is_jpy = "JPY" in asset_key
    step = 1.0 if is_jpy else 0.5
    
    # Build trigger list: start from opt, go down
    triggers = []
    t = opt_trigger
    while t >= 1.0:
        triggers.append(round(t, 1))
        t -= step
    
    # Also try going UP to confirm baseline
    triggers_up = []
    t = opt_trigger + step
    while t <= opt_trigger * 1.5:
        triggers_up.append(round(t, 1))
        t += step
    
    all_triggers = triggers_up + triggers  # high-to-low
    
    print("  {}: Sweeping T1 trigger from {} to {} ({} steps)".format(
        asset_key, max(all_triggers), min(all_triggers), len(all_triggers)))
    
    results = []
    best_under_81 = None
    best_at_or_above_81 = None
    
    for trig in sorted(all_triggers, reverse=True):
        r = run_pair_with_trigger(asset_key, native, trig)
        if r is None:
            continue
        r["t1_trigger"] = trig
        results.append(r)
        
        tr_day = r["trades"] / r["days"] if r["days"] else 0
        flag = "OK" if r["wr"] >= WR_FLOOR else "LOW"
        print("    T1={:>5.1f} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | {:>5.1f}p | Tr/d {:>4.2f} {}".format(
            trig, r["trades"], r["wr"], r["pf"], r["pnl"], tr_day, flag))
        
        if r["wr"] >= WR_FLOOR:
            if best_at_or_above_81 is None or r["trades"] > best_at_or_above_81["trades"]:
                best_at_or_above_81 = r
        else:
            if best_under_81 is None or r["trades"] < best_under_81["trades"]:
                best_under_81 = r
    
    # ── FINE TUNE: binary search between last good and first bad ──────
    if best_at_or_above_81 and best_under_81:
        lo = best_under_81["t1_trigger"]
        hi = best_at_or_above_81["t1_trigger"]
        print("  {}: Fine-tuning between {} and {}".format(asset_key, lo, hi))
        
        for _ in range(5):  # 5 iterations of binary search
            mid = round((lo + hi) / 2, 2)
            if mid == lo or mid == hi:
                break
            r = run_pair_with_trigger(asset_key, native, mid)
            if r is None:
                break
            r["t1_trigger"] = mid
            results.append(r)
            
            tr_day = r["trades"] / r["days"] if r["days"] else 0
            flag = "OK" if r["wr"] >= WR_FLOOR else "LOW"
            print("    T1={:>5.2f} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | Tr/d {:>4.2f} {}".format(
                mid, r["trades"], r["wr"], r["pf"], tr_day, flag))
            
            if r["wr"] >= WR_FLOOR:
                hi = mid
                if best_at_or_above_81 is None or r["trades"] > best_at_or_above_81["trades"]:
                    best_at_or_above_81 = r
            else:
                lo = mid
                if best_under_81 is None or r["trades"] < best_under_81["trades"]:
                    best_under_81 = r
    
    if best_at_or_above_81:
        tr_day = best_at_or_above_81["trades"] / best_at_or_above_81["days"] if best_at_or_above_81["days"] else 0
        print("  {} [OPTIMAL] T1={} | {}tr | {:.1f}% WR | PF {:.2f} | Tr/d {:.2f}".format(
            asset_key, best_at_or_above_81["t1_trigger"], best_at_or_above_81["trades"],
            best_at_or_above_81["wr"], best_at_or_above_81["pf"], tr_day))
    
    return results


if __name__ == '__main__':
    import sys
    
    # Can run single pair or all
    if len(sys.argv) > 1:
        target_pairs = sys.argv[1].split(",")
    else:
        target_pairs = ["EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD"]
    
    print("=" * 80)
    print("TRIGGER SWEEP — Max Trades Before WR < 81%")
    print("AR Expansion: {:.1f}x | Cutoff: 4PM EST | WR Floor: {:.0f}%".format(AR_EXPANSION, WR_FLOOR))
    print("=" * 80)
    print("")
    
    all_results = {}
    for asset in target_pairs:
        print("--- {} ---".format(asset))
        results = sweep_pair(asset)
        all_results[asset] = results
        print("")
    
    # ── FINAL SUMMARY ────────────────────────────────────────────────────
    print("=" * 80)
    print("FINAL SUMMARY — Max Trades at WR >= 81%")
    print("=" * 80)
    print("{:<10} {:>7} {:>6} {:>8} {:>8} {:>8} {:>8}".format(
        "Asset", "T1_Trig", "Trades", "WR%", "PF", "MaxDD", "Tr/Day"))
    print("-" * 80)
    
    for asset in target_pairs:
        results = all_results.get(asset, [])
        best = None
        for r in results:
            if r["wr"] >= WR_FLOOR:
                if best is None or r["trades"] > best["trades"]:
                    best = r
        if best:
            tr_day = best["trades"] / best["days"] if best["days"] else 0
            print("{:<10} {:>7.2f} {:>6} {:>7.1f}% {:>8.2f} {:>8.1f} {:>8.2f}".format(
                asset, best["t1_trigger"], best["trades"], best["wr"], best["pf"], best["max_dd"], tr_day))
        else:
            print("{:<10} {:>7} {:>6} {:>8} {:>8} {:>8} {:>8}".format(
                asset, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"))
    
    # Save results
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trigger_sweep_results.json")
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print("\nResults saved to: {}".format(out_path))
