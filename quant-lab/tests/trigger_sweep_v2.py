"""
TRIGGER SWEEP — Max Trades Before WR < 81% (v2)
================================================
Targeted sweep: coarse steps then binary search.
Tracks EVERY config tried for combinatorics/portfolio analysis.
"""
import sys, os, json, time

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')

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
WR_FLOOR = 81.0


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
                "t1_trigger": t1_trigger, "tiers": optimized_tiers}

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
        "trades": len(trades), "days": result.data_days, "wr": wr,
        "pnl": result.total_pnl_pips, "pf": result.profit_factor,
        "avg_w": result.avg_win_pips, "avg_l": result.avg_loss_pips,
        "exp": result.expectancy_pips, "max_dd": result.max_drawdown_pips,
        "max_cw": max_cw, "max_cl": max_cl, "t1_trigger": t1_trigger,
        "tiers": optimized_tiers,
    }


def sweep_pair(asset_key):
    native = NATIVE_CONFIGS[asset_key]
    csv_path = os.path.join(DATA_DIR, native["csv"])
    if not os.path.exists(csv_path):
        print("  {}: MISSING DATA".format(asset_key), flush=True)
        return []

    opt_trigger = round(native["tiers"]["T1"]["trigger"] * 0.833, 1)
    is_jpy = "JPY" in asset_key
    step = 1.0 if is_jpy else 1.0  # Use 1.0 for all to keep it manageable

    # Phase 1: Coarse sweep from opt down to 1.0 in larger steps
    # Start with opt, then go down by 2.0 steps to find the rough boundary
    coarse_triggers = []
    t = opt_trigger
    while t >= 1.0:
        coarse_triggers.append(round(t, 1))
        t -= 2.0
    if coarse_triggers[-1] > 1.0:
        coarse_triggers.append(1.0)

    print("  {}: Coarse sweep {} triggers ({} to {})".format(
        asset_key, len(coarse_triggers), max(coarse_triggers), min(coarse_triggers)), flush=True)

    results = []
    last_good = None
    first_bad = None

    for trig in sorted(coarse_triggers, reverse=True):
        t0 = time.time()
        r = run_pair_with_trigger(asset_key, native, trig)
        elapsed = time.time() - t0
        if r is None:
            continue
        r["t1_trigger"] = trig
        results.append(r)

        tr_day = r["trades"] / r["days"] if r["days"] else 0
        flag = "OK" if r["wr"] >= WR_FLOOR else "LOW"
        print("    T1={:>5.1f} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | {:>6.1f}p PnL | MaxDD {:>5.1f}p | MaxCL {} | Tr/d {:>4.2f} | {:.0f}s | {}".format(
            trig, r["trades"], r["wr"], r["pf"], r["pnl"], r["max_dd"], r["max_cl"], tr_day, elapsed, flag), flush=True)

        if r["wr"] >= WR_FLOOR:
            last_good = r
        else:
            if first_bad is None:
                first_bad = r
            break  # Once we hit WR < 81%, stop coarse sweep

    # Phase 2: Fine sweep between last good and first bad (or below last good if no bad)
    if last_good and first_bad:
        lo = first_bad["t1_trigger"]
        hi = last_good["t1_trigger"]
        print("  {}: Fine sweep between {} and {}".format(asset_key, lo, hi), flush=True)

        fine_triggers = []
        t = hi - step
        while t > lo:
            fine_triggers.append(round(t, 1))
            t -= step

        for trig in fine_triggers:
            t0 = time.time()
            r = run_pair_with_trigger(asset_key, native, trig)
            elapsed = time.time() - t0
            if r is None:
                continue
            r["t1_trigger"] = trig
            results.append(r)

            tr_day = r["trades"] / r["days"] if r["days"] else 0
            flag = "OK" if r["wr"] >= WR_FLOOR else "LOW"
            print("    T1={:>5.1f} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | {:>6.1f}p PnL | MaxDD {:>5.1f}p | MaxCL {} | Tr/d {:>4.2f} | {:.0f}s | {}".format(
                trig, r["trades"], r["wr"], r["pf"], r["pnl"], r["max_dd"], r["max_cl"], tr_day, elapsed, flag), flush=True)

            if r["wr"] >= WR_FLOOR:
                last_good = r
            else:
                first_bad = r
                break

    # Phase 3: Binary search for precision
    if last_good and first_bad:
        lo = first_bad["t1_trigger"]
        hi = last_good["t1_trigger"]
        print("  {}: Binary search between {:.1f} and {:.1f}".format(asset_key, lo, hi), flush=True)

        for i in range(4):
            mid = round((lo + hi) / 2, 2)
            if abs(mid - lo) < 0.1 or abs(mid - hi) < 0.1:
                break
            t0 = time.time()
            r = run_pair_with_trigger(asset_key, native, mid)
            elapsed = time.time() - t0
            if r is None:
                break
            r["t1_trigger"] = mid
            results.append(r)

            tr_day = r["trades"] / r["days"] if r["days"] else 0
            flag = "OK" if r["wr"] >= WR_FLOOR else "LOW"
            print("    T1={:>5.2f} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | {:>6.1f}p PnL | MaxDD {:>5.1f}p | MaxCL {} | Tr/d {:>4.2f} | {:.0f}s | {}".format(
                mid, r["trades"], r["wr"], r["pf"], r["pnl"], r["max_dd"], r["max_cl"], tr_day, elapsed, flag), flush=True)

            if r["wr"] >= WR_FLOOR:
                hi = mid
                last_good = r
            else:
                lo = mid
                first_bad = r

    if last_good:
        tr_day = last_good["trades"] / last_good["days"] if last_good["days"] else 0
        print("  {} [BEST] T1={} | {}tr | {:.1f}% WR | PF {:.2f} | PnL {:.1f}p | MaxDD {:.1f}p | MaxCL {} | Tr/d {:.2f}".format(
            asset_key, last_good["t1_trigger"], last_good["trades"],
            last_good["wr"], last_good["pf"], last_good["pnl"], last_good["max_dd"],
            last_good["max_cl"], tr_day), flush=True)

    return results


if __name__ == '__main__':
    if len(sys.argv) > 1:
        target_pairs = sys.argv[1].split(",")
    else:
        target_pairs = ["EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURNZD", "EURCHF", "EURCAD"]

    print("=" * 100, flush=True)
    print("TRIGGER SWEEP v2 — Max Trades Before WR < 81%", flush=True)
    print("AR Expansion: {:.1f}x | Cutoff: 4PM EST | WR Floor: {:.0f}%".format(AR_EXPANSION, WR_FLOOR), flush=True)
    print("=" * 100, flush=True)
    print("", flush=True)

    all_results = {}
    for asset in target_pairs:
        print("--- {} ---".format(asset), flush=True)
        t_start = time.time()
        results = sweep_pair(asset)
        all_results[asset] = results
        print("  {} total runs in {:.0f}s".format(len(results), time.time() - t_start), flush=True)
        print("", flush=True)

    # ── FINAL SUMMARY ────────────────────────────────────────────────────
    print("=" * 100, flush=True)
    print("FINAL SUMMARY — Max Trades at WR >= 81%", flush=True)
    print("=" * 100, flush=True)
    print("{:<10} {:>7} {:>6} {:>8} {:>8} {:>8} {:>8} {:>6} {:>8} {:>8} {:>8}".format(
        "Asset", "T1_Trig", "Trades", "WR%", "PF", "PnL(p)", "MaxDD(p)", "MaxCL", "MaxCW", "Tr/Day", "AvgExp"), flush=True)
    print("-" * 100, flush=True)

    total_trades = 0
    total_pnl = 0
    for asset in target_pairs:
        results = all_results.get(asset, [])
        best = None
        for r in results:
            if r["wr"] >= WR_FLOOR:
                if best is None or r["trades"] > best["trades"]:
                    best = r
        if best:
            tr_day = best["trades"] / best["days"] if best["days"] else 0
            print("{:<10} {:>7.2f} {:>6} {:>7.1f}% {:>8.2f} {:>8.1f} {:>8.1f} {:>6} {:>8} {:>8.2f} {:>8.2f}".format(
                asset, best["t1_trigger"], best["trades"], best["wr"], best["pf"],
                best["pnl"], best["max_dd"], best["max_cl"], best["max_cw"], tr_day, best["exp"]), flush=True)
            total_trades += best["trades"]
            total_pnl += best["pnl"]
        else:
            print("{:<10} {:>7} {:>6} {:>8} {:>8} {:>8} {:>8} {:>6} {:>8} {:>8} {:>8}".format(
                asset, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"), flush=True)

    print("-" * 100, flush=True)
    print("{:<10} {:>7} {:>6} {:>8} {:>8} {:>8.1f}".format(
        "BASKET", "", total_trades, "", "", total_pnl), flush=True)

    # ── FULL CONFIG LOG (for combinatorics) ──────────────────────────────
    print("", flush=True)
    print("=" * 100, flush=True)
    print("FULL CONFIG LOG — Every Config Tried (for combinatorics / portfolio)", flush=True)
    print("=" * 100, flush=True)

    for asset in target_pairs:
        results = all_results.get(asset, [])
        if not results:
            continue
        print("", flush=True)
        print("--- {} ---".format(asset), flush=True)
        print("  {:>7} | {:>6} | {:>7} | {:>6} | {:>8} | {:>7} | {:>5} | {:>6} | {:>5}".format(
            "T1_Trig", "Trades", "WR%", "PF", "PnL(p)", "MaxDD(p)", "MaxCL", "Tr/Day", "Status"), flush=True)
        print("  " + "-" * 85, flush=True)
        for r in sorted(results, key=lambda x: x["t1_trigger"], reverse=True):
            tr_day = r["trades"] / r["days"] if r["days"] else 0
            status = "OK" if r["wr"] >= WR_FLOOR else "LOW"
            print("  {:>7.2f} | {:>6} | {:>6.1f}% | {:>6.2f} | {:>8.1f} | {:>7.1f} | {:>5} | {:>6.2f} | {:>5}".format(
                r["t1_trigger"], r["trades"], r["wr"], r["pf"], r["pnl"], r["max_dd"],
                r["max_cl"], tr_day, status), flush=True)

    # Save results
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trigger_sweep_results.json")
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print("", flush=True)
    print("Results saved to: {}".format(out_path), flush=True)
