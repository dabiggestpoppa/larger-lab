"""
CRYPTO TRIGGER SWEEP — BTCUSD & ETHUSD
========================================
Uses native configs from asset_configs.py (the Bible):
  BTCUSD: pip=1.0, T1 au=205 trig=246 ar_max=750, SL_buffer=25
  ETHUSD: pip=1.0, T1 au=35 trig=42 ar_max=70, SL_buffer=5

Floor sweep: max trades before WR < 81%
Ceiling sweep: max accuracy, PF >= 10.0, min 0.5 tr/day
Also sweeps raw triggers for SOL/XRP/BNB discovery (data permitting).

Usage:
  python trigger_sweep_crypto.py              # BTC + ETH
  python trigger_sweep_crypto.py BTCUSD       # one pair
"""
import sys, os, json, time

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

from symmetry_trap_backtest import SymmetryTrapBacktest

DATA_DIR = os.path.join(QUANTLAB_ROOT, 'data')
REPORTS_DIR = os.path.join(QUANTLAB_ROOT, 'reports')

# ─── NATIVE CONFIGS FROM asset_configs.py (the Bible) ───────────────────
# BTCUSD: pip_value=1.0 (engine convention, NOT MT5 pip)
#   T1: ar_max=750, au=205, trigger=246, gear: T2@654 T3@1392
#   SL method: FIXED_BUFFER, buffer=25p
# ETHUSD: pip_value=1.0
#   T1: ar_max=70, au=35, trigger=42, gear: T2@52 T3@65
#   SL method: FIXED_BUFFER, buffer=5p

NATIVE_CONFIGS = {
    "BTCUSD": {
        "csv": "BTCUSD_M5.csv",
        "pip_value": 1.0,
        "sl_buffer": 25.0,
        "tiers": {
            "T1": {"ar_max": 750.0, "au": 205.0, "trigger": 246.0},
            "T2": {"ar_max": 1700.0, "au": 545.0, "trigger": 654.0},
            "T3": {"ar_max": 3000.0, "au": 1160.0, "trigger": 1392.0},
        },
    },
    "ETHUSD": {
        "csv": "ETHUSD_M5.csv",
        "pip_value": 1.0,
        "sl_buffer": 5.0,
        "tiers": {
            "T1": {"ar_max": 70.0, "au": 35.0, "trigger": 42.0},
            "T2": {"ar_max": 105.0, "au": 42.0, "trigger": 52.0},
            "T3": {"ar_max": 160.0, "au": 52.0, "trigger": 65.0},
        },
    },
}

AR_EXPANSION = 3.0
WR_FLOOR = 81.0
PF_FLOOR = 10.0
MIN_TR_PER_DAY = 0.5


def apply_vector_with_trigger(native_tiers, trigger_override):
    """Scale all tier triggers proportionally to T1 override."""
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
    """Run a single backtest with given T1 trigger override."""
    csv_path = os.path.join(DATA_DIR, native_config["csv"])
    if not os.path.exists(csv_path):
        print("  {}: MISSING DATA at {}".format(asset_key, csv_path), flush=True)
        return None

    optimized_tiers = apply_vector_with_trigger(native_config["tiers"], t1_trigger)

    bt = SymmetryTrapBacktest(
        pip_size=native_config["pip_value"],
        tier_config=optimized_tiers,
        symbol=asset_key,
        config={"pip_value": native_config["pip_value"], "tiers": optimized_tiers, "name": asset_key}
    )
    bt.session_cutoff = 16

    result = bt.run_from_csv(csv_path)
    trades = result.trades

    if not trades:
        return {
            "trades": 0, "wr": 0, "pnl": 0, "pf": 0, "max_dd": 0, "max_cl": 0,
            "avg_w": 0, "avg_l": 0, "exp": 0, "max_cw": 0, "days": result.data_days,
            "t1_trigger": t1_trigger, "tiers": optimized_tiers, "tr_per_day": 0,
        }

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


def sweep_floor(asset_key):
    """Floor sweep: start low (many trades), go up until WR < 81%."""
    native = NATIVE_CONFIGS[asset_key]
    csv_path = os.path.join(DATA_DIR, native["csv"])
    if not os.path.exists(csv_path):
        print("  {}: MISSING DATA — skipping".format(asset_key), flush=True)
        return []

    native_t1 = native["tiers"]["T1"]["trigger"]
    # Start from a fraction of native trigger (more trades)
    start_trigger = max(10, int(native_t1 * 0.3))
    print("  {}: FLOOR sweep from T1={} upward (native T1={})".format(
        asset_key, start_trigger, native_t1), flush=True)

    results = []
    last_good = None
    step = max(10, int(native_t1 * 0.15))
    t = start_trigger

    while t <= native_t1 * 2.5:
        r = run_pair_with_trigger(asset_key, native, t)
        if r is None:
            t += step
            continue
        results.append(r)
        tr_day = r["tr_per_day"]
        flag = "OK" if r["wr"] >= WR_FLOOR else "LOW"
        print("    [FLOOR] T1={:>6} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | {:>8.1f}p | Tr/d {:>4.2f} | {}".format(
            t, r["trades"], r["wr"], r["pf"], r["pnl"], tr_day, flag), flush=True)

        if r["wr"] >= WR_FLOOR:
            last_good = r
        else:
            break
        t += step

    if last_good:
        print("  {} [FLOOR BEST] T1={} | {}tr | {:.1f}% WR | PF {:.2f} | Tr/d {:.2f}".format(
            asset_key, last_good["t1_trigger"], last_good["trades"],
            last_good["wr"], last_good["pf"], last_good["tr_per_day"]), flush=True)
    else:
        print("  {} [FLOOR] No config found with WR >= 81%".format(asset_key), flush=True)

    return results


def sweep_ceiling(asset_key):
    """Ceiling sweep: start at native, go up to find max accuracy."""
    native = NATIVE_CONFIGS[asset_key]
    csv_path = os.path.join(DATA_DIR, native["csv"])
    if not os.path.exists(csv_path):
        print("  {}: MISSING DATA — skipping".format(asset_key), flush=True)
        return []

    native_t1 = native["tiers"]["T1"]["trigger"]
    print("  {}: CEILING sweep from T1={} upward".format(asset_key, native_t1), flush=True)

    results = []
    peak_wr = 0
    peak_trigger = None
    peak_tr_per_day = 0

    step = max(20, int(native_t1 * 0.2))
    t = native_t1
    max_t = native_t1 * 3.0
    stop_sweep = False

    while t <= max_t and not stop_sweep:
        r = run_pair_with_trigger(asset_key, native, t)
        if r is None:
            t += step
            continue
        results.append(r)
        valid = r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY
        status = "OK" if valid else "FAIL"
        print("    [CEILING] T1={:>6} | {:>5}tr | {:>5.1f}% WR | PF {:>5.2f} | {:>8.1f}p | Tr/d {:>4.2f} | {}".format(
            t, r["trades"], r["wr"], r["pf"], r["pnl"], r["tr_per_day"], status), flush=True)

        if valid:
            if r["wr"] > peak_wr or (r["wr"] == peak_wr and r["tr_per_day"] > peak_tr_per_day):
                peak_wr = r["wr"]
                peak_trigger = t
                peak_tr_per_day = r["tr_per_day"]
        else:
            if r["tr_per_day"] < MIN_TR_PER_DAY * 0.3:
                stop_sweep = True
        t += step

    if peak_trigger:
        best_r = [r for r in results if r["t1_trigger"] == peak_trigger][0]
        print("  {} [CEILING BEST] T1={} | {:.1f}% WR | PF {:.2f} | Tr/d {:.2f}".format(
            asset_key, peak_trigger, peak_wr, best_r["pf"], peak_tr_per_day), flush=True)
    else:
        print("  {} [CEILING] No valid config found (PF>=10, >=0.5 tr/day)".format(asset_key), flush=True)

    return results


# ─── MAIN ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) > 1:
        target_pairs = [p.strip().upper() for p in sys.argv[1].split(",")]
    else:
        target_pairs = ["BTCUSD", "ETHUSD"]

    print("=" * 100, flush=True)
    print("CRYPTO TRIGGER SWEEP — BTCUSD & ETHUSD", flush=True)
    print("Configs from asset_configs.py (the Bible) | AR Expansion: {:.1f}x".format(AR_EXPANSION), flush=True)
    print("WR Floor: {:.0f}% | PF Floor: {:.0f} | Min Tr/Day: {:.1f}".format(WR_FLOOR, PF_FLOOR, MIN_TR_PER_DAY), flush=True)
    print("=" * 100, flush=True)

    all_floor = {}
    all_ceiling = {}

    for asset in target_pairs:
        if asset not in NATIVE_CONFIGS:
            print("\n>>> {} — NO CONFIG IN BIBLE, skipping".format(asset), flush=True)
            continue

        print("\n" + "=" * 100, flush=True)
        print(">>> {} — FLOOR SWEEP".format(asset), flush=True)
        print("=" * 100, flush=True)
        t0 = time.time()
        floor_results = sweep_floor(asset)
        all_floor[asset] = floor_results
        print("  {} floor: {} runs in {:.0f}s".format(asset, len(floor_results), time.time() - t0), flush=True)

        print("\n" + "=" * 100, flush=True)
        print(">>> {} — CEILING SWEEP".format(asset), flush=True)
        print("=" * 100, flush=True)
        t0 = time.time()
        ceiling_results = sweep_ceiling(asset)
        all_ceiling[asset] = ceiling_results
        print("  {} ceiling: {} runs in {:.0f}s".format(asset, len(ceiling_results), time.time() - t0), flush=True)

    # ── FINAL SUMMARY ────────────────────────────────────────────────────
    print("\n" + "=" * 100, flush=True)
    print("CRYPTO SWEEP — FINAL SUMMARY", flush=True)
    print("=" * 100, flush=True)

    print("\n--- FLOOR (Max Trades, WR >= 81%) ---", flush=True)
    print("{:<10} {:>8} {:>6} {:>8} {:>8} {:>10} {:>8} {:>8}".format(
        "Asset", "T1_Trig", "Trades", "WR%", "PF", "PnL(p)", "MaxDD(p)", "Tr/Day"), flush=True)
    print("-" * 80, flush=True)
    for asset in target_pairs:
        results = all_floor.get(asset, [])
        best = None
        for r in results:
            if r["wr"] >= WR_FLOOR:
                if best is None or r["trades"] > best["trades"]:
                    best = r
        if best:
            print("{:<10} {:>8} {:>6} {:>7.1f}% {:>8.2f} {:>10.1f} {:>8.1f} {:>8.2f}".format(
                asset, best["t1_trigger"], best["trades"], best["wr"], best["pf"],
                best["pnl"], best["max_dd"], best["tr_per_day"]), flush=True)
        else:
            print("{:<10} NO VALID CONFIG".format(asset), flush=True)

    print("\n--- CEILING (Max Accuracy, PF>=10, >=0.5 tr/day) ---", flush=True)
    print("{:<10} {:>8} {:>6} {:>8} {:>8} {:>10} {:>8} {:>8}".format(
        "Asset", "T1_Trig", "Trades", "WR%", "PF", "PnL(p)", "MaxDD(p)", "Tr/Day"), flush=True)
    print("-" * 80, flush=True)
    for asset in target_pairs:
        results = all_ceiling.get(asset, [])
        valid = [r for r in results if r["pf"] >= PF_FLOOR and r["tr_per_day"] >= MIN_TR_PER_DAY]
        if valid:
            best = max(valid, key=lambda r: (r["wr"], r["tr_per_day"]))
            print("{:<10} {:>8} {:>6} {:>7.1f}% {:>8.2f} {:>10.1f} {:>8.1f} {:>8.2f}".format(
                asset, best["t1_trigger"], best["trades"], best["wr"], best["pf"],
                best["pnl"], best["max_dd"], best["tr_per_day"]), flush=True)
        else:
            print("{:<10} NO VALID CONFIG".format(asset), flush=True)

    # Save results
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_path = os.path.join(REPORTS_DIR, 'trigger_sweep_crypto.json')
    serializable = {"floor": {}, "ceiling": {}}
    for asset in target_pairs:
        serializable["floor"][asset] = [{k: v for k, v in r.items() if k != "tiers"} for r in all_floor.get(asset, [])]
        serializable["ceiling"][asset] = [{k: v for k, v in r.items() if k != "tiers"} for r in all_ceiling.get(asset, [])]
    with open(out_path, 'w') as f:
        json.dump(serializable, f, indent=2)
    print("\nFull results saved to: {}".format(out_path), flush=True)
