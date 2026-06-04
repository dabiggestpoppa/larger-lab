"""
TRIGGER SWEEP v2 — USD Basket
==============================
USDCAD, USDCHF, USDJPY
"""
import sys, os, json, time

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')

NATIVE_CONFIGS = {
    "USDCAD": {
        "csv": "USDCAD_PRO_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 28.0, "au": 14.0, "trigger": 17.0},
                  "T2": {"ar_max": 42.0, "au": 18.0, "trigger": 21.0},
                  "T3": {"ar_max": 68.0, "au": 22.0, "trigger": 27.0}},
    },
    "USDCHF": {
        "csv": "USDCHF_M5.csv",
        "pip_value": 0.0001,
        "tiers": {"T1": {"ar_max": 24.0, "au": 12.0, "trigger": 14.0},
                  "T2": {"ar_max": 36.0, "au": 15.0, "trigger": 18.0},
                  "T3": {"ar_max": 58.0, "au": 19.0, "trigger": 23.0}},
    },
    "USDJPY": {
        "csv": "USDJPY_M5.csv",
        "pip_value": 0.01,
        "tiers": {"T1": {"ar_max": 30.0, "au": 15.0, "trigger": 18.0},
                  "T2": {"ar_max": 45.0, "au": 19.0, "trigger": 23.0},
                  "T3": {"ar_max": 72.0, "au": 24.0, "trigger": 29.0}},
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
    best_ok = None
    first_fail = None
    for t1 in coarse_triggers:
        r = run_pair_with_trigger(asset_key, native, t1)
        if r is None: continue
        results.append(r)
        status = "OK" if r["wr"] >= WR_FLOOR else "LOW"
        tr_per_day = r["trades"]/r["days"] if r["days"] else 0
        print("    T1={:>5} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | {:>7.1f}p PnL | MaxDD {:>5.1f}p | MaxCL {} | Tr/d {:>4.2f} | {}".format(
            t1, r["trades"], r["wr"], r["pf"], r["pnl"], r["max_dd"], r["max_cl"],
            tr_per_day, status), flush=True)
        if r["wr"] >= WR_FLOOR:
            best_ok = t1
        elif first_fail is None:
            first_fail = t1
            break
    if best_ok is None:
        print("  {}: ALL configs below WR floor!".format(asset_key), flush=True)
        return results
    if first_fail is None:
        print("  {}: All coarse OK, extending...".format(asset_key), flush=True)
        t = coarse_triggers[-1] - 2.0
        while t >= 1.0:
            r = run_pair_with_trigger(asset_key, native, t)
            if r:
                results.append(r)
                status = "OK" if r["wr"] >= WR_FLOOR else "LOW"
                tr_per_day = r["trades"]/r["days"] if r["days"] else 0
                print("    T1={:>5} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | Tr/d {:>4.2f} | {}".format(
                    t, r["trades"], r["wr"], r["pf"], tr_per_day, status), flush=True)
                if r["wr"] >= WR_FLOOR: best_ok = t
                else: first_fail = t; break
            t -= 2.0
    if first_fail is None or best_ok is None:
        print("  {}: Could not find boundary".format(asset_key), flush=True)
        return results
    print("  {}: Fine sweep between {} and {}".format(asset_key, first_fail, best_ok), flush=True)
    fine_low = min(best_ok, first_fail)
    fine_high = max(best_ok, first_fail)
    t = fine_high - 1.0
    while t > fine_low:
        r = run_pair_with_trigger(asset_key, native, round(t, 1))
        if r:
            results.append(r)
            status = "OK" if r["wr"] >= WR_FLOOR else "LOW"
            tr_per_day = r["trades"]/r["days"] if r["days"] else 0
            print("    T1={:>5} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | Tr/d {:>4.2f} | {}".format(
                t, r["trades"], r["wr"], r["pf"], tr_per_day, status), flush=True)
            if r["wr"] >= WR_FLOOR: best_ok = t
            else: first_fail = t
        t -= 1.0
    print("  {}: Binary search between {} and {}".format(asset_key, first_fail, best_ok), flush=True)
    for _ in range(4):
        mid = round((best_ok + first_fail) / 2, 2)
        if mid == best_ok or mid == first_fail: break
        r = run_pair_with_trigger(asset_key, native, mid)
        if r:
            results.append(r)
            status = "OK" if r["wr"] >= WR_FLOOR else "LOW"
            tr_per_day = r["trades"]/r["days"] if r["days"] else 0
            print("    T1={:>5} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | Tr/d {:>4.2f} | {}".format(
                mid, r["trades"], r["wr"], r["pf"], tr_per_day, status), flush=True)
            if r["wr"] >= WR_FLOOR: best_ok = mid
            else: first_fail = mid
    ok_results = [r for r in results if r["wr"] >= WR_FLOOR]
    if ok_results:
        best = max(ok_results, key=lambda r: r["trades"])
        tr_per_day = best["trades"]/best["days"] if best["days"] else 0
        print("  {} [BEST] T1={} | {}tr | {:.1f}% WR | PF {:.2f} | PnL {:.1f}p | MaxDD {:.1f}p | MaxCL {} | Tr/d {:.2f}".format(
            asset_key, best["t1_trigger"], best["trades"], best["wr"], best["pf"],
            best["pnl"], best["max_dd"], best["max_cl"], tr_per_day), flush=True)
    print("  {} total runs: {}".format(asset_key, len(results)), flush=True)
    return results


if __name__ == '__main__':
    print("=" * 80)
    print("TRIGGER SWEEP v2 — USD Basket")
    print("AR Expansion: 3.0x | Cutoff: 4PM EST | WR Floor: 81%")
    print("=" * 80)
    all_results = {}
    for asset in ["USDCAD", "USDCHF", "USDJPY"]:
        print("\n--- {} ---".format(asset))
        all_results[asset] = sweep_pair(asset)
    out_path = os.path.join(QUANTLAB_ROOT, 'reports', 'trigger_sweep_usd.json')
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
    print("SUMMARY — USD Basket")
    print("=" * 80)
    print("{:<10} {:>6} {:>8} {:>10} {:>8} {:>8} {:>6} {:>8}".format(
        "Asset", "Trades", "WR%", "PnL", "PF", "MaxDD", "MaxCL", "Tr/Day"))
    print("-" * 80)
    total_trades = 0
    for asset in ["USDCAD", "USDCHF", "USDJPY"]:
        if all_results[asset]:
            ok = [r for r in all_results[asset] if r["wr"] >= WR_FLOOR]
            if ok:
                best = max(ok, key=lambda r: r["trades"])
                tr_per_day = best["trades"]/best["days"] if best["days"] else 0
                print("{:<10} {:>6} {:>7.1f}% {:>10.1f} {:>8.2f} {:>8.1f} {:>6} {:>8.2f}".format(
                    asset, best["trades"], best["wr"], best["pnl"], best["pf"],
                    best["max_dd"], best["max_cl"], tr_per_day))
                total_trades += best["trades"]
    print("-" * 80)
    print("{:<10} {:>6}".format("TOTAL", total_trades))
